import time
from datetime import datetime
import pytz
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from core.models import Customer, Vendor, MenuItem, Order
from core.decorators import vendor_required, customer_required
from core.utils import (
    enhanced_notifications,
    twilio_notifications,
    notifier,
)

IST = pytz.timezone('Asia/Kolkata')


def home(request):
    return render(request, 'landing.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def sign_in(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if role == 'customer':
            customer = Customer.objects.filter(email=username).first()
            if not customer:
                customer = Customer.objects.filter(phone=username).first()

            if customer and customer.check_password(password):
                request.session['user_id'] = customer.id
                request.session['user_name'] = customer.full_name
                request.session['user_email'] = customer.email
                request.session['user_role'] = 'customer'
                messages.success(request, 'Login successful!')
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
                return redirect('sign_in')

        elif role == 'vendor':
            vendor = Vendor.objects.filter(email=username).first()
            if vendor and vendor.check_password(password):
                request.session['user_id'] = vendor.id
                request.session['user_name'] = vendor.business_name
                request.session['user_email'] = vendor.email
                request.session['user_role'] = 'vendor'
                messages.success(request, 'Login successful!')
                return redirect('vendor_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
                return redirect('sign_in')

    return render(request, 'sign_in.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    response = redirect('home')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def signup_success(request):
    return render(request, 'success.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        customer = Customer.objects.filter(email=email).first()
        vendor = Vendor.objects.filter(email=email).first()

        if customer or vendor:
            reset_token = str(int(time.time()))
            reset_link = f"http://127.0.0.1:8000/reset-password/{reset_token}?email={email}"
            print("\n=== PASSWORD RESET LINK ===")
            print(f"Email: {email}")
            print(f"Reset Link: {reset_link}")
            print("==============================\n")
            messages.success(request, 'Password reset link has been printed to terminal!')
        else:
            messages.error(request, 'Email not found in our records.')

        return redirect('forgot_password')

    return render(request, 'forgot_password.html')


def reset_password(request, token):
    email = request.GET.get('email', '')

    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect(f"/reset-password/{token}?email={email}")

        customer = Customer.objects.filter(email=email).first()
        vendor = Vendor.objects.filter(email=email).first()

        if customer:
            customer.set_password(new_password)
            customer.save()
            messages.success(request, 'Password updated successfully!')
        elif vendor:
            vendor.set_password(new_password)
            vendor.save()
            messages.success(request, 'Password updated successfully!')
        else:
            messages.error(request, 'Invalid reset link!')

        return redirect('sign_in')

    return render(request, 'reset_password.html', {'token': token, 'email': email})


def admin_delete_vendors_page(request):
    return render(request, 'admin/delete_vendors.html')


@csrf_exempt
def admin_delete_all_vendors(request):
    if request.method == 'POST':
        try:
            MenuItem.objects.all().delete()
            orders = Order.objects.all()
            for order in orders:
                if order.vendor_id:
                    order.vendor_name = f"Deleted Vendor (ID: {order.vendor_id})"
                    order.vendor_id = None
                    order.save()

            vendor_count = Vendor.objects.count()
            Vendor.objects.all().delete()

            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {vendor_count} vendors and all associated menu items',
                'deleted_count': vendor_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def twilio_webhook(request):
    if request.method != 'POST':
        return HttpResponse('', status=200)

    try:
        from_number = request.POST.get('From')
        message_body = request.POST.get('Body')
        print(f"Received WhatsApp message from {from_number}: {message_body}")

        action, order_id, reason = twilio_notifications.process_vendor_whatsapp_reply(from_number, message_body)

        if action and order_id:
            vendor_phone = from_number.replace('whatsapp:', '') if from_number.startswith('whatsapp:') else from_number
            vendor = Vendor.objects.filter(phone=vendor_phone).first()
            if not vendor:
                twilio_notifications.send_confirmation_whatsapp(
                    from_number, "❌ Phone number not registered as vendor. Please contact support."
                )
                return HttpResponse('', status=200)

            order = Order.objects.filter(id=order_id, vendor_id=vendor.id).first()
            if not order:
                twilio_notifications.send_confirmation_whatsapp(
                    from_number, f"❌ Order #{order_id} not found or not assigned to your shop."
                )
                return HttpResponse('', status=200)

            if order.status != 'Pending':
                twilio_notifications.send_confirmation_whatsapp(
                    from_number, f"❌ Order #{order_id} has already been processed (Status: {order.status})."
                )
                return HttpResponse('', status=200)

            current_time = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)

            if action == 'accept':
                order.status = 'preparing'
                order.preparing_at = current_time
                order.save()

                enhanced_notifications.send_dual_notification(
                    from_number, f"✅ Order #{order_id} ACCEPTED and marked as preparing. Customer has been notified."
                )
                customer = Customer.objects.filter(id=order.customer_id).first()
                if customer:
                    order_data = {'id': order.id, 'vendor_name': order.vendor_name}
                    enhanced_notifications.notify_customer_order_status(customer.phone, order_data, 'accepted')

            elif action == 'reject':
                order.status = 'Rejected'
                order.rejection_reason = reason
                order.rejected_at = current_time
                order.save()

                enhanced_notifications.send_dual_notification(
                    from_number, f"❌ Order #{order_id} REJECTED. Customer has been notified."
                )
                customer = Customer.objects.filter(id=order.customer_id).first()
                if customer:
                    order_data = {'id': order.id, 'vendor_name': order.vendor_name, 'rejection_reason': reason}
                    enhanced_notifications.notify_customer_order_status(customer.phone, order_data, 'Rejected')

        else:
            enhanced_notifications.send_dual_notification(
                from_number, "❓ Invalid format. Use:\n• ACCEPT [order_id]\n• REJECT [order_id] [reason]"
            )

        return HttpResponse('', status=200)
    except Exception as e:
        print(f"Error processing Twilio WhatsApp webhook: {e}")
        return HttpResponse('', status=500)


@csrf_exempt
@vendor_required
def test_twilio_notification(request):
    try:
        vendor = Vendor.objects.filter(id=request.session['user_id']).first()
        test_message = f"📱 TEST NOTIFICATION from LocalConnect!\n\nHi {vendor.business_name},\nYour SMS and WhatsApp notifications are working correctly.\n\nTime: {datetime.now(IST).strftime('%I:%M %p')}"
        result = enhanced_notifications.send_dual_notification(vendor.phone, test_message, 'test')
        if result.get('sms') or result.get('whatsapp'):
            return JsonResponse({'success': True, 'message': 'Test notifications sent successfully!', 'details': result})
        return JsonResponse({'success': False, 'error': 'Both SMS and WhatsApp failed', 'details': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@customer_required
def test_customer_notification(request):
    try:
        customer = Customer.objects.filter(id=request.session['user_id']).first()
        test_message = f"📱 TEST NOTIFICATION from LocalConnect!\n\nHi {customer.full_name},\nYour SMS and WhatsApp notifications are working correctly.\n\nYou'll receive updates about your orders on both channels.\n\nTime: {datetime.now(IST).strftime('%I:%M %p')}"
        result = enhanced_notifications.send_dual_notification(customer.phone, test_message, 'test')
        if result.get('sms') or result.get('whatsapp'):
            return JsonResponse({'success': True, 'message': 'Test notifications sent successfully!', 'details': result})
        return JsonResponse({'success': False, 'error': 'Both SMS and WhatsApp failed', 'details': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
