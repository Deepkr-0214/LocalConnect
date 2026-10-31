import json
from datetime import datetime
import pytz
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Min, Max, Avg, Count, Q
from django.conf import settings
from django.utils import timezone

from core.models import Customer, Vendor, MenuItem, Order
from core.decorators import customer_required
from core.utils import (
    notifier,
    enhanced_notifications,
    twilio_notifications,
    razorpay_client,
)
from core.chatbot_logic import chat_logic
from utils.geocoding import geocode_address

IST = pytz.timezone('Asia/Kolkata')


def customer_signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('customer_signup')

        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('customer_signup')

        if phone and not phone.startswith('+91'):
            if phone.startswith('91'):
                phone = f"+{phone}"
            else:
                phone = f"+91{phone.lstrip('0')}"

        new_customer = Customer(full_name=full_name, email=email, phone=phone)
        new_customer.set_password(password)
        new_customer.save()

        request.session['user_id'] = new_customer.id
        request.session['user_name'] = new_customer.full_name
        request.session['user_email'] = new_customer.email
        request.session['user_role'] = 'customer'

        try:
            notifier.notify_customer_order_placed(phone, {
                'id': 'WELCOME',
                'vendor_name': 'LocalConnect',
                'total': '0'
            })
        except Exception as e:
            print(f"Failed to send welcome notification: {e}")

        messages.success(request, 'Signup successful!')
        return redirect('customer_dashboard')

    return render(request, 'customer/sign_up.html')


@customer_required
def customer_dashboard(request):
    user_id = request.session.get('user_id')
    return render(request, 'customer/base.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id
    })


def _get_category_vendors_data(categories, default_min=100, default_max=300, default_icon='🏪'):
    if isinstance(categories, str):
        vendors = Vendor.objects.filter(business_category=categories)
    else:
        vendors = Vendor.objects.filter(business_category__in=categories)

    vendors_data = []
    for v in vendors:
        price_stats = MenuItem.objects.filter(vendor=v).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        min_price = int(price_stats['min_price']) if price_stats['min_price'] else default_min
        max_price = int(price_stats['max_price']) if price_stats['max_price'] else default_max

        rating_stats = Order.objects.filter(
            vendor=v,
            review_rating__isnull=False,
            status='Completed'
        ).aggregate(
            avg_rating=Avg('review_rating'),
            review_count=Count('review_rating')
        )
        avg_rating = round(rating_stats['avg_rating'], 1) if rating_stats['avg_rating'] else 0
        review_count = rating_stats['review_count'] if rating_stats['review_count'] else 0

        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if v.business_sub_category else v.business_category,
            'is_open': bool(v.is_open),
            'shop_image': v.shop_image or default_icon,
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude,
            'longitude': v.longitude,
            'rating': avg_rating,
            'review_count': review_count
        })
    return vendors_data


@customer_required
def food_restaurants(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    food_categories = [
        'Food & Restaurant', 'Street Food', 'Food Shop', 'Restaurant',
        'Dhaba', 'Street Food Carts', 'Food Shops', 'Restaurants & Dhabas'
    ]
    vendors_data = _get_category_vendors_data(food_categories, 100, 300, '🏪')

    return render(request, 'customer/food&rest.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def garage(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Garage', 250, 500, '🔧')

    return render(request, 'customer/garage.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def electronics(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Electronics', 150, 600, '⚡')

    return render(request, 'customer/electronics.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def fashion(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Fashion', 200, 800, '👗')

    return render(request, 'customer/fashion.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def grocery(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Grocery', 50, 200, '🛒')

    return render(request, 'customer/grocery.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def pharmacy(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Pharmacy', 20, 150, '💊')

    return render(request, 'customer/pharmacy.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def books(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    customer_lat = customer.latitude if customer else None
    customer_lon = customer.longitude if customer else None

    vendors_data = _get_category_vendors_data('Books', 80, 250, '📚')

    return render(request, 'customer/books.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'vendors': vendors_data,
        'customer_lat': customer_lat,
        'customer_lon': customer_lon,
    })


@customer_required
def customer_orders(request):
    user_id = request.session.get('user_id')
    orders_query = Order.objects.filter(customer_id=user_id).order_by('-created_at')
    orders = [{
        'id': o.id,
        'vendor_id': o.vendor_id,
        'vendor_name': o.vendor_name,
        'items': o.items,
        'delivery_type': o.delivery_type,
        'payment_type': o.payment_type,
        'total': o.total,
        'status': o.status,
        'created_at': o.created_at.isoformat() if o.created_at else '',
        'preparing_at': o.preparing_at.isoformat() if o.preparing_at else None,
        'out_for_delivery_at': o.out_for_delivery_at.isoformat() if o.out_for_delivery_at else None,
        'ready_at': o.ready_at.isoformat() if o.ready_at else None,
        'completed_at': o.completed_at.isoformat() if o.completed_at else None,
        'review_rating': o.review_rating,
        'review_comment': o.review_comment,
        'rejectionReason': o.rejection_reason
    } for o in orders_query]

    return render(request, 'customer/orders.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id,
        'orders': orders,
        'orders_query': orders_query
    })


@customer_required
def customer_profile(request):
    user_id = request.session.get('user_id')
    customer = Customer.objects.filter(id=user_id).first()
    return render(request, 'customer/profile.html', {
        'user_name': request.session.get('user_name'),
        'customer': customer,
        'user_id': user_id
    })


@customer_required
def vendor_details(request, vendor_id):
    user_id = request.session.get('user_id')
    vendor = get_object_or_404(Vendor, id=vendor_id)
    return render(request, 'customer/viewdet.html', {
        'vendor_id': vendor_id,
        'vendor': vendor,
        'user_name': request.session.get('user_name'),
        'user_id': user_id
    })


@customer_required
def vendor_map(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if not vendor.latitude or not vendor.longitude:
        messages.warning(request, 'Location not available for this vendor')
        return redirect('vendor_details', vendor_id=vendor_id)
    return render(request, 'customer/map_view.html', {'vendor_id': vendor_id})


@customer_required
def map_vendor(request, vendor_id):
    return redirect('vendor_map', vendor_id=vendor_id)


@customer_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        customer = Customer.objects.filter(id=request.session['user_id']).first()

        if not customer.check_password(current_password):
            messages.error(request, 'Current password is incorrect!')
            return redirect('customer_change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('customer_change_password')

        customer.set_password(new_password)
        customer.save()

        messages.success(request, 'Password changed successfully!')
        return redirect('customer_profile')

    return render(request, 'customer/change_password.html')


@csrf_exempt
@customer_required
def delete_customer_account(request):
    if request.method == 'POST':
        try:
            customer_id = request.session['user_id']
            customer = Customer.objects.filter(id=customer_id).first()
            if not customer:
                return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)

            Order.objects.filter(customer_id=customer_id).delete()
            customer.delete()
            request.session.flush()

            return JsonResponse({
                'success': True,
                'message': 'Account permanently deleted',
                'redirect': '/'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@customer_required
def customer_notification_settings(request):
    user_id = request.session.get('user_id')
    return render(request, 'customer/notification_settings.html', {
        'user_name': request.session.get('user_name'),
        'user_id': user_id
    })


@csrf_exempt
@customer_required
def save_customer_notification_settings(request):
    return JsonResponse({'success': True, 'message': 'Settings saved successfully'})


def amount_to_words(amount):
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def convert_below_hundred(n):
        if n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        else:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')

    def convert_below_thousand(n):
        if n < 100:
            return convert_below_hundred(n)
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_below_hundred(n % 100) if n % 100 != 0 else '')

    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    result = ''

    if rupees == 0:
        result = 'Zero Rupees'
    else:
        if rupees >= 10000000:
            crores = rupees // 10000000
            result += convert_below_thousand(crores) + ' Crore '
            rupees %= 10000000
        if rupees >= 100000:
            lakhs = rupees // 100000
            result += convert_below_thousand(lakhs) + ' Lakh '
            rupees %= 100000
        if rupees >= 1000:
            thousands = rupees // 1000
            result += convert_below_thousand(thousands) + ' Thousand '
            rupees %= 1000
        if rupees > 0:
            result += convert_below_thousand(rupees) + ' '
        result += 'Rupees'

    if paise > 0:
        result += ' and ' + convert_below_hundred(paise) + ' Paise'

    return result.strip() + ' Only'


@customer_required
def invoice(request, order_id):
    user_id = request.session.get('user_id')
    order = Order.objects.filter(id=order_id, customer_id=user_id).first()

    if not order:
        messages.error(request, 'Order not found')
        return redirect('customer_orders')

    if order.status != 'Completed':
        messages.warning(request, 'Invoice is only available for completed orders')
        return redirect('customer_orders')

    vendor = Vendor.objects.filter(id=order.vendor_id).first()
    customer = Customer.objects.filter(id=user_id).first()

    if not vendor or not customer:
        messages.error(request, 'Unable to generate invoice')
        return redirect('customer_orders')

    items = order.get_items()
    amount_words = amount_to_words(order.total)

    context = {
        'order': order,
        'vendor': vendor,
        'customer': customer,
        'items': items,
        'amount_words': amount_words,
        'item_count': len(items),
        'invoice_date': timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
    }
    return render(request, 'customer/invoice.html', context)


# --- Customer API Endpoints ---

@csrf_exempt
@customer_required
def create_order(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        customer = Customer.objects.filter(id=request.session['user_id']).first()
        vendor = Vendor.objects.filter(id=data['vendor_id']).first()

        if not vendor:
            return JsonResponse({'error': 'Vendor not found'}, status=404)

        if not vendor.phone or not vendor.phone.startswith('+91'):
            return JsonResponse({'error': 'Vendor phone number is not configured properly'}, status=500)

        if not customer.phone or not customer.phone.startswith('+91'):
            return JsonResponse({'error': 'Customer phone number is not configured properly'}, status=500)

        location_type = data.get('locationType')
        if data.get('deliveryType') == 'delivery' and not location_type:
            location_type = 'home'

        customer_delivery_lat = None
        customer_delivery_lon = None

        if data.get('deliveryType') == 'delivery':
            if location_type == 'current':
                customer_delivery_lat = customer.current_latitude or customer.latitude
                customer_delivery_lon = customer.current_longitude or customer.longitude
            else:
                customer_delivery_lat = customer.home_latitude or customer.latitude
                customer_delivery_lon = customer.home_longitude or customer.longitude

        order = Order(
            customer_id=request.session['user_id'],
            vendor_id=vendor.id,
            vendor_name=vendor.business_name,
            customer_name=customer.full_name,
            customer_phone=customer.phone,
            delivery_type=data['deliveryType'],
            payment_type=data['paymentType'],
            order_type=data['deliveryType'],
            total=data['total'],
            discount_amount=data.get('discount', 0),
            offer_title=data.get('offerTitle', ''),
            customer_suggestion=data.get('customerSuggestion', ''),
            status='Pending' if data['paymentType'] != 'online' else 'Payment Pending',
            delivery_location_type=location_type,
            vendor_latitude=vendor.latitude,
            vendor_longitude=vendor.longitude,
            customer_delivery_latitude=customer_delivery_lat,
            customer_delivery_longitude=customer_delivery_lon
        )
        order.set_items(data['items'])
        order.save()

        if data['paymentType'] != 'online':
            order_data = {
                'id': order.id,
                'customer_name': customer.full_name,
                'customer_phone': customer.phone,
                'vendor_name': vendor.business_name,
                'items_summary': order.items_summary,
                'total': order.total,
                'delivery_type': order.delivery_type,
                'payment_type': order.payment_type
            }
            try:
                notifier.notify_customer_order_placed(customer.phone, order_data)
                notifier.notify_vendor_new_order(vendor.phone, order_data)
            except Exception as e:
                print(f"Failed to send enhanced notifications: {e}")

        return JsonResponse({'success': True, 'order_id': order.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@customer_required
def cancel_order(request, order_id):
    order = Order.objects.filter(id=order_id, customer_id=request.session['user_id']).first()
    if order and order.status == 'Pending':
        order.status = 'cancelled'
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Cannot cancel'}, status=400)


@csrf_exempt
@customer_required
def create_payment(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        order_id = data.get('order_id')
        order = Order.objects.filter(id=order_id).first()

        if not order:
            return JsonResponse({'error': 'Order not found'}, status=404)

        amount = int(order.total * 100)

        if not razorpay_client:
            return JsonResponse({'error': 'Razorpay not configured'}, status=500)

        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        })

        order.razorpay_order_id = razorpay_order['id']
        order.save()

        return JsonResponse({
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'amount': amount,
            'customer_name': order.customer_name,
            'customer_email': request.session.get('user_email', ''),
            'customer_phone': order.customer_phone
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@customer_required
def verify_payment(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        order_id = data.get('order_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            if razorpay_client:
                razorpay_client.utility.verify_payment_signature(params_dict)

            order = Order.objects.filter(id=order_id, razorpay_order_id=razorpay_order_id).first()
            if order:
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.status = 'Pending'
                order.save()

                vendor = Vendor.objects.filter(id=order.vendor_id).first()
                customer = Customer.objects.filter(id=order.customer_id).first()
                if vendor and customer:
                    order_data = {
                        'id': order.id,
                        'customer_name': order.customer_name,
                        'customer_phone': customer.phone,
                        'vendor_name': order.vendor_name,
                        'items_summary': order.items_summary,
                        'total': order.total,
                        'delivery_type': order.delivery_type,
                        'payment_type': order.payment_type
                    }
                    try:
                        notifier.notify_customer_order_placed(customer.phone, order_data)
                        notifier.notify_vendor_new_order(vendor.phone, order_data)
                    except Exception as e:
                        print(f"Failed to send enhanced payment notifications: {e}")

                return JsonResponse({'success': True})
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as sig_error:
            return JsonResponse({'success': False, 'error': 'Invalid signature'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@customer_required
def delete_order(request, order_id):
    if request.method == 'DELETE':
        order = Order.objects.filter(id=order_id, customer_id=request.session['user_id']).first()
        if order and (order.status == 'cancelled' or order.status == 'delivered'):
            order.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Cannot delete'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def mark_response_helpful(request, order_id):
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)
    order.response_helpful = (order.response_helpful or 0) + 1
    order.save()
    return JsonResponse({'success': True, 'helpful_count': order.response_helpful})


@csrf_exempt
@customer_required
def mark_order_received(request, order_id):
    order = Order.objects.filter(id=order_id, customer_id=request.session['user_id']).first()
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)
    if order.status != 'out_for_delivery':
        return JsonResponse({'error': 'Order is not out for delivery'}, status=400)

    order.status = 'Completed'
    order.completed_at = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
    order.save()

    return JsonResponse({
        'success': True,
        'message': 'Order marked as received',
        'earnings_added': order.total,
        'vendor_id': order.vendor_id,
        'vendor_name': order.vendor_name
    })


@csrf_exempt
@customer_required
def add_review(request, order_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    order = Order.objects.filter(id=order_id, customer_id=request.session['user_id']).first()
    if order:
        order.review_rating = data.get('rating')
        order.review_comment = data.get('comment')
        order.review_date = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Order not found'}, status=404)


@csrf_exempt
@customer_required
def update_profile(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    customer = Customer.objects.filter(id=request.session['user_id']).first()
    if customer:
        if 'full_name' in data:
            customer.full_name = data['full_name']
            request.session['user_name'] = data['full_name']
        if 'email' in data:
            customer.email = data['email']
            request.session['user_email'] = data['email']
        if 'phone' in data:
            customer.phone = data['phone']

        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        pincode = data.get('pincode')

        customer.address = address
        customer.city = city
        customer.state = state
        customer.pincode = pincode

        if address:
            full_address = f"{address}, {city}, {state}, {pincode}".strip(', ')
            latitude, longitude = geocode_address(full_address)
            if latitude and longitude:
                customer.latitude = latitude
                customer.longitude = longitude

        customer.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Customer not found'}, status=404)


@csrf_exempt
@customer_required
def set_home_location(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    customer = Customer.objects.filter(id=request.session['user_id']).first()
    if customer:
        customer.home_latitude = data.get('home_latitude')
        customer.home_longitude = data.get('home_longitude')
        customer.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Customer not found'}, status=404)


@csrf_exempt
@customer_required
def update_current_location(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    customer = Customer.objects.filter(id=request.session['user_id']).first()
    if customer:
        customer.current_latitude = data.get('current_latitude')
        customer.current_longitude = data.get('current_longitude')
        customer.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Customer not found'}, status=404)


@csrf_exempt
@customer_required
def update_customer_profile(request):
    return update_profile(request)


@csrf_exempt
@customer_required
def sms_order_received(request):
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        order_id = data.get('order_id')
        order = Order.objects.filter(id=order_id, customer_id=request.session['user_id']).first()
        if not order:
            return JsonResponse({'error': 'Order not found'}, status=404)

        if order.status != 'out_for_delivery':
            return JsonResponse({'error': 'Order is not out for delivery'}, status=400)

        order.status = 'Completed'
        order.completed_at = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
        order.save()

        customer = Customer.objects.filter(id=request.session['user_id']).first()
        vendor = Vendor.objects.filter(id=order.vendor_id).first()

        confirmation_message = f"✅ Order #{order.id} marked as received!\n\nThank you for choosing {order.vendor_name}!\nTotal: ₹{order.total}\n\nPlease rate your experience on our app."
        twilio_notifications.send_confirmation_sms(customer.phone, confirmation_message)

        if vendor:
            vendor_message = f"🎉 Order #{order.id} completed!\n\nCustomer: {order.customer_name}\nTotal: ₹{order.total}\nEarnings added to your account."
            twilio_notifications.send_confirmation_sms(vendor.phone, vendor_message)

        return JsonResponse({
            'success': True,
            'message': 'Order marked as received',
            'earnings_added': order.total,
            'vendor_id': order.vendor_id,
            'vendor_name': order.vendor_name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_vendor_menu(request, vendor_id):
    items = MenuItem.objects.filter(vendor_id=vendor_id)
    return JsonResponse([{
        'id': item.id,
        'name': item.name,
        'sub_name': item.sub_name,
        'category': item.category,
        'price': item.price,
        'is_available': bool(item.is_available),
        'image_file': item.image_file
    } for item in items], safe=False)


def search_vendors(request):
    search_term = request.GET.get('q', '').strip().lower()
    if not search_term:
        return JsonResponse([], safe=False)

    vendor_matches = list(Vendor.objects.filter(
        Q(business_name__icontains=search_term) | Q(business_category__icontains=search_term)
    ))

    vendor_ids_by_menu = MenuItem.objects.filter(
        name__icontains=search_term
    ).values_list('vendor_id', flat=True).distinct()
    dish_matches = list(Vendor.objects.filter(id__in=vendor_ids_by_menu))

    all_matched_vendors = list({v.id: v for v in (vendor_matches + dish_matches)}.values())

    vendors_data = []
    for v in all_matched_vendors:
        matching_dishes = list(MenuItem.objects.filter(
            vendor_id=v.id,
            name__icontains=search_term
        ).values_list('name', flat=True))

        rating_stats = Order.objects.filter(
            vendor_id=v.id,
            review_rating__isnull=False,
            status='Completed'
        ).aggregate(
            avg_rating=Avg('review_rating'),
            review_count=Count('review_rating')
        )
        avg_rating = round(rating_stats['avg_rating'], 1) if rating_stats['avg_rating'] else 0
        review_count = rating_stats['review_count'] if rating_stats['review_count'] else 0

        price_stats = MenuItem.objects.filter(vendor_id=v.id).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        min_price = int(price_stats['min_price']) if price_stats['min_price'] else 100
        max_price = int(price_stats['max_price']) if price_stats['max_price'] else 300

        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if v.business_sub_category else v.business_category,
            'cuisine': v.business_sub_category if v.business_sub_category else v.business_category,
            'rating': avg_rating,
            'reviews': review_count,
            'image': v.shop_image,
            'isOpen': bool(v.is_open),
            'latitude': v.latitude,
            'longitude': v.longitude,
            'priceRange': f"₹{min_price}-{max_price}",
            'deliveryTime': '15-25 min',
            'matching_dishes': matching_dishes
        })

    return JsonResponse(vendors_data, safe=False)


def get_vendor_all_reviews(request, vendor_id):
    reviews = Order.objects.filter(
        vendor_id=vendor_id,
        review_rating__isnull=False,
        status='Completed'
    ).order_by('-review_date')

    return JsonResponse([{
        'customer_name': review.customer_name,
        'rating': review.review_rating,
        'comment': review.review_comment,
        'date': review.review_date.isoformat() if review.review_date else (review.created_at.isoformat() if review.created_at else ''),
        'vendor_response': review.vendor_response,
        'response_date': review.vendor_response_date.isoformat() if review.vendor_response_date else None,
        'helpful_count': review.response_helpful or 0,
        'vendor_name': review.vendor_name
    } for review in reviews], safe=False)


def get_vendor_reviews(request, vendor_id):
    rating_stats = Order.objects.filter(
        vendor_id=vendor_id,
        review_rating__isnull=False,
        status='Completed'
    ).aggregate(
        avg_rating=Avg('review_rating'),
        review_count=Count('review_rating')
    )
    return JsonResponse({
        'avg_rating': round(rating_stats['avg_rating'], 1) if rating_stats['avg_rating'] else 4.5,
        'review_count': rating_stats['review_count'] if rating_stats['review_count'] else 0
    })


@csrf_exempt
@customer_required
def chat(request):
    resp = chat_logic(request)
    if isinstance(resp, JsonResponse):
        try:
            data = json.loads(resp.content.decode('utf-8'))
            if 'reply' in data and 'response' not in data:
                data['response'] = data['reply']
                return JsonResponse(data, status=resp.status_code)
        except Exception:
            pass
    return resp
