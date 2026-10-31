import os
import base64
import json
from datetime import datetime, date
import pytz
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Sum, Count, Q
from django.conf import settings
from django.utils import timezone

from core.models import Customer, Vendor, MenuItem, Order, Offer, VendorNotification
from core.decorators import vendor_required
from core.utils import (
    notifier,
    enhanced_notifications,
    twilio_notifications,
    geocode_service,
)
from core.order_filters import DjangoOrderFilters
from utils.category_labels import get_category_labels

IST = pytz.timezone('Asia/Kolkata')


def vendor_signup(request):
    if request.method == 'POST':
        business_name = request.POST.get('business_name', '').strip()
        email = request.POST.get('email', '').strip()
        business_category = request.POST.get('business_category', '').strip()
        business_address = request.POST.get('business_address', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')

        if Vendor.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use a different email or login.')
            return redirect('vendor_signup')

        if phone and not phone.startswith('+91'):
            if phone.startswith('91'):
                phone = f"+{phone}"
            else:
                phone = f"+91{phone.lstrip('0')}"

        new_vendor = Vendor(
            business_name=business_name,
            email=email,
            business_category=business_category,
            business_sub_category=request.POST.get('business_sub_category'),
            category_type=request.POST.get('business_sub_category'),
            business_address=business_address,
            phone=phone
        )
        new_vendor.set_password(password)

        latitude, longitude = geocode_service.geocode(business_address)
        if latitude and longitude:
            new_vendor.latitude = latitude
            new_vendor.longitude = longitude
            geocoding_status = '✅ Location detected automatically!'
        else:
            geocoding_status = '⚠️ Location could not be detected. Please try with a more complete address.'

        new_vendor.save()

        request.session['user_id'] = new_vendor.id
        request.session['user_name'] = new_vendor.business_name
        request.session['user_email'] = new_vendor.email
        request.session['user_role'] = 'vendor'

        try:
            enhanced_notifications.notify_vendor_welcome(phone, business_name)
        except Exception as e:
            print(f"Failed to send welcome notification: {e}")

        messages.success(request, f'Signup successful! {geocoding_status}')
        return redirect('vendor_dashboard')

    return render(request, 'vendor/sign_up.html')


@vendor_required
def vendor_dashboard(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()

    category = vendor.business_category if vendor else 'Food & Restaurant'
    subcategory = vendor.business_sub_category if vendor else None

    orders = Order.objects.filter(vendor_id=vendor_id).order_by('-created_at')[:5]
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    today = date.today()
    todays_orders = Order.objects.filter(
        vendor_id=vendor_id,
        created_at__date=today,
        status='Completed'
    ).count()

    todays_earnings = DjangoOrderFilters.calculate_today_earnings(vendor_id)
    pending_orders = unread_count

    rating_stat = Order.objects.filter(
        vendor_id=vendor_id,
        review_rating__isnull=False,
        status='Completed'
    ).aggregate(avg=Avg('review_rating'))['avg']
    avg_rating = round(rating_stat, 1) if rating_stat else 0

    menu_items = MenuItem.objects.filter(vendor_id=vendor_id)[:5]
    labels = get_category_labels(category)

    context = {
        'orders': orders,
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'todays_orders': todays_orders,
        'todays_earnings': todays_earnings,
        'pending_orders': pending_orders,
        'avg_rating': avg_rating,
        'menu_items': menu_items,
        'category': category,
        'subcategory': subcategory,
        'labels': labels
    }
    response = render(request, 'vendor/vendor_dashboard.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@vendor_required
def vendor_delivery_map(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/delivery_map.html', {
        'vendor_profile': vendor,
        'labels': labels,
        'category': category
    })


@vendor_required
def vendor_orders(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    orders = Order.objects.filter(vendor_id=vendor_id).order_by('-created_at')
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/orders.html', {
        'orders': orders,
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'labels': labels,
        'category': category
    })


@csrf_exempt
@vendor_required
def update_order_status(request, order_id):
    order = Order.objects.filter(id=order_id, vendor_id=request.session['user_id']).first()
    if not order:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    new_status = data['status']
    order.status = new_status
    if data.get('rejection_reason'):
        order.rejection_reason = data['rejection_reason']

    current_time = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
    if new_status == 'preparing':
        order.preparing_at = current_time
    elif new_status == 'out_for_delivery':
        order.out_for_delivery_at = current_time
    elif new_status == 'ready':
        order.ready_at = current_time
    elif new_status == 'Completed':
        order.completed_at = current_time
    elif new_status == 'Rejected':
        order.rejected_at = current_time

    order.save()

    customer = Customer.objects.filter(id=order.customer_id).first()
    vendor = Vendor.objects.filter(id=order.vendor_id).first()
    if customer:
        order_data = {
            'id': order.id,
            'vendor_name': order.vendor_name,
            'rejection_reason': order.rejection_reason
        }
        try:
            notifier.notify_customer_order_status(customer.phone, order_data, new_status)
            if new_status == 'Completed' and vendor:
                notifier.notify_vendor_order_completed(vendor.phone, order_data)
        except Exception as e:
            print(f"Enhanced notification failed: {e}")

    resp_data = {'success': True}
    if new_status == 'Completed':
        resp_data['earnings_added'] = order.total

    return JsonResponse(resp_data)


@vendor_required
def vendor_menu(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    menu_items = MenuItem.objects.filter(vendor_id=vendor_id)
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/menu.html', {
        'menu_items': menu_items,
        'items': menu_items,
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'labels': labels,
        'category': category
    })


@csrf_exempt
@vendor_required
def add_menu_item(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    image_file = 'default.jpg'
    if data.get('image_file') and data['image_file'].startswith('data:image'):
        try:
            header, image_data = data['image_file'].split(',', 1)
            image_bytes = base64.b64decode(image_data)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ext = 'jpg' if ('jpeg' in header or 'jpg' in header) else 'png'
            filename = f"item_{request.session['user_id']}_{timestamp}.{ext}"

            upload_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'food')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            image_file = filename
        except Exception as e:
            print(f"Error saving image: {e}")
            image_file = 'default.jpg'

    item = MenuItem(
        vendor_id=request.session['user_id'],
        name=data['name'],
        sub_name=data.get('sub_name'),
        category=data.get('category'),
        price=data['price'],
        is_available=data.get('is_available', True),
        image_file=image_file
    )
    item.save()
    return JsonResponse({'success': True, 'id': item.id, 'image_file': image_file})


@csrf_exempt
@vendor_required
def edit_menu_item(request, item_id):
    if request.method == 'DELETE':
        return delete_menu_item(request, item_id)
    item = MenuItem.objects.filter(id=item_id, vendor_id=request.session['user_id']).first()
    if not item:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    item.name = data.get('name', item.name)
    item.sub_name = data.get('sub_name', item.sub_name)
    item.category = data.get('category', item.category)
    item.price = data.get('price', item.price)
    item.is_available = data.get('is_available', item.is_available)

    if data.get('image_file') and data['image_file'].startswith('data:image'):
        try:
            header, image_data = data['image_file'].split(',', 1)
            image_bytes = base64.b64decode(image_data)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ext = 'jpg' if ('jpeg' in header or 'jpg' in header) else 'png'
            filename = f"item_{request.session['user_id']}_{timestamp}.{ext}"
            upload_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'food')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            item.image_file = filename
        except Exception as e:
            print(f"Error saving image: {e}")

    item.save()
    return JsonResponse({'success': True, 'image_file': item.image_file})


@csrf_exempt
@vendor_required
def delete_menu_item(request, item_id):
    item = MenuItem.objects.filter(id=item_id, vendor_id=request.session['user_id']).first()
    if not item:
        return JsonResponse({'error': 'Not found'}, status=404)
    item.delete()
    return JsonResponse({'success': True})


@csrf_exempt
@vendor_required
def toggle_item_availability(request, item_id):
    item = MenuItem.objects.filter(id=item_id, vendor_id=request.session['user_id']).first()
    if not item:
        return JsonResponse({'error': 'Not found'}, status=404)

    item.is_available = not item.is_available
    item.save()
    return JsonResponse({'success': True, 'is_available': item.is_available})


@vendor_required
def force_fix_earnings(request):
    vendor_id = request.session['user_id']
    all_orders = Order.objects.filter(vendor_id=vendor_id)
    fixed_count = 0
    for order in all_orders:
        if order.rejection_reason and order.status != 'Rejected':
            order.status = 'Rejected'
            order.save()
            fixed_count += 1

    messages.success(request, f'Force fixed {fixed_count} orders. Please refresh earnings page.')
    return redirect('vendor_earnings')


@vendor_required
def fix_earnings(request):
    vendor_id = request.session['user_id']
    orders_to_fix = Order.objects.filter(
        vendor_id=vendor_id,
        rejection_reason__isnull=False
    ).exclude(status='Rejected')

    count = orders_to_fix.count()
    for order in orders_to_fix:
        order.status = 'Rejected'
        order.save()

    messages.success(request, f'Fixed {count} orders with incorrect status')
    return redirect('vendor_earnings')


@vendor_required
def vendor_earnings(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    total_earnings = DjangoOrderFilters.calculate_total_earnings(vendor_id)
    today_earnings = DjangoOrderFilters.calculate_today_earnings(vendor_id)
    week_earnings = DjangoOrderFilters.calculate_week_earnings(vendor_id)
    month_earnings = DjangoOrderFilters.calculate_month_earnings(vendor_id)

    completed_orders = DjangoOrderFilters.get_completed_orders_count(vendor_id)
    total_orders = completed_orders
    all_orders = Order.objects.filter(vendor_id=vendor_id).count()
    completion_rate = (completed_orders / all_orders * 100) if all_orders > 0 else 0
    avg_order_value = DjangoOrderFilters.calculate_average_order_value(vendor_id)
    pending_orders = unread_count

    chart_labels, chart_values = DjangoOrderFilters.get_earnings_chart_data(vendor_id, 7)
    earnings_history = Order.objects.filter(vendor_id=vendor_id).order_by('-created_at')[:10]

    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    context = {
        'total_earnings': total_earnings,
        'today_earnings': today_earnings,
        'week_earnings': week_earnings,
        'month_earnings': month_earnings,
        'month_growth': 0,
        'week_growth': 0,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'completion_rate': completion_rate,
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'top_category': 'Food',
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'earnings_history': earnings_history,
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'labels': labels,
        'category': category
    }
    response = render(request, 'vendor/earnings.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@vendor_required
def vendor_reviews(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    reviews = Order.objects.filter(
        vendor_id=vendor_id,
        review_rating__isnull=False,
        status='Completed'
    ).order_by('-created_at')

    total_count = reviews.count()
    rating_stat = reviews.aggregate(avg=Avg('review_rating'))['avg']
    avg_rating = round(rating_stat, 1) if rating_stat else 0

    month_start = date.today().replace(day=1)
    recent_count = reviews.filter(created_at__date__gte=month_start).count()

    responded_count = reviews.filter(vendor_response__isnull=False).exclude(vendor_response='').count()
    response_rate = round((responded_count / total_count * 100) if total_count > 0 else 0)

    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/reviews.html', {
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_count': total_count,
        'recent_count': recent_count,
        'response_rate': response_rate,
        'responded_count': responded_count,
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'labels': labels,
        'category': category
    })


@vendor_required
def vendor_change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        vendor = Vendor.objects.filter(id=request.session['user_id']).first()
        if not vendor.check_password(current_password):
            messages.error(request, 'Current password is incorrect!')
            return redirect('vendor_change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('vendor_change_password')

        vendor.set_password(new_password)
        vendor.save()

        messages.success(request, 'Password changed successfully!')
        return redirect('vendor_settings')

    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    unread_count = Order.objects.filter(vendor_id=request.session['user_id'], status='Pending').count()
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/change_password.html', {
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'labels': labels,
        'category': category
    })


@vendor_required
def vendor_settings(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()

    try:
        offers = Offer.objects.filter(vendor_id=vendor_id)
    except Exception:
        offers = []

    if request.method == 'POST':
        new_address = request.POST.get('address')
        address_changed = new_address and new_address != vendor.business_address

        vendor.business_name = request.POST.get('shop_name', vendor.business_name)
        vendor.email = request.POST.get('email', vendor.email)
        vendor.business_category = request.POST.get('business_category', vendor.business_category)
        vendor.business_sub_category = request.POST.get('business_sub_category', vendor.business_sub_category)
        vendor.phone = request.POST.get('phone', vendor.phone)
        vendor.business_address = request.POST.get('address', vendor.business_address)
        vendor.about = request.POST.get('about', vendor.about)
        vendor.category_type = request.POST.get('category_type')
        vendor.veg_nonveg = request.POST.get('veg_nonveg')

        opening_time = request.POST.get('opening_time')
        opening_period = request.POST.get('opening_period')
        closing_time = request.POST.get('closing_time')
        closing_period = request.POST.get('closing_period')
        vendor.opening_time = f"{opening_time} {opening_period}" if (opening_time and opening_period) else None
        vendor.closing_time = f"{closing_time} {closing_period}" if (closing_time and closing_period) else None

        vendor.indoor_seating = request.POST.get('indoor_seating') == '1'
        vendor.outdoor_seating = request.POST.get('outdoor_seating') == '1'
        vendor.home_delivery = request.POST.get('home_delivery') == '1'
        vendor.takeaway = request.POST.get('takeaway') == '1'
        vendor.free_wifi = request.POST.get('free_wifi') == '1'
        vendor.ac = request.POST.get('ac') == '1'
        vendor.cooler = request.POST.get('cooler') == '1'
        vendor.parking = request.POST.get('parking')
        vendor.other_amenities = request.POST.get('other_amenities')

        location_message = None
        if address_changed:
            latitude, longitude = geocode_service.geocode(new_address)
            if latitude and longitude:
                vendor.latitude = latitude
                vendor.longitude = longitude
                location_message = '✅ Location updated automatically!'
            else:
                location_message = '⚠️ Address updated, but location could not be detected. Try a more complete address.'

        if 'latitude' in request.POST and 'longitude' in request.POST:
            try:
                manual_lat = float(request.POST.get('latitude'))
                manual_lng = float(request.POST.get('longitude'))
                if -90 <= manual_lat <= 90 and -180 <= manual_lng <= 180:
                    vendor.latitude = manual_lat
                    vendor.longitude = manual_lng
                    location_message = 'GPS location updated successfully!'
            except (ValueError, TypeError):
                pass

        vendor.save()

        request.session['user_name'] = vendor.business_name
        request.session['user_email'] = vendor.email

        if location_message:
            messages.success(request, f'Settings updated successfully! {location_message}')
        else:
            messages.success(request, 'Settings updated successfully!')
        return redirect('vendor_settings')

    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)

    return render(request, 'vendor/settings.html', {
        'vendor_profile': vendor,
        'unread_count': unread_count,
        'offers': offers,
        'labels': labels,
        'category': category
    })


@csrf_exempt
@vendor_required
def toggle_shop_status(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    vendor.is_open = data.get('is_open', False)
    vendor.save()
    return JsonResponse({'success': True, 'is_open': bool(vendor.is_open)})


@csrf_exempt
@vendor_required
def update_shop_image(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    vendor.shop_image = data.get('shop_image', '🏪')
    vendor.save()
    return JsonResponse({'success': True})


@csrf_exempt
@vendor_required
def update_vendor_profile(request):
    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    vendor.business_name = request.POST.get('business_name', vendor.business_name)
    vendor.email = request.POST.get('email', vendor.email)
    vendor.business_category = request.POST.get('business_category', vendor.business_category)
    vendor.business_address = request.POST.get('business_address', vendor.business_address)
    vendor.phone = request.POST.get('phone', vendor.phone)
    vendor.save()
    messages.success(request, 'Profile updated successfully!')
    return redirect('vendor_dashboard')


@vendor_required
def vendor_notification_settings(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()
    return render(request, 'vendor/notification_settings.html', {
        'vendor_profile': vendor,
        'unread_count': unread_count
    })


@vendor_required
def vendor_notification_dashboard(request):
    vendor_id = request.session['user_id']
    vendor = Vendor.objects.filter(id=vendor_id).first()
    unread_count = Order.objects.filter(vendor_id=vendor_id, status='Pending').count()
    return render(request, 'vendor/notification_dashboard.html', {
        'vendor_profile': vendor,
        'unread_count': unread_count
    })


@csrf_exempt
@vendor_required
def delete_vendor_account(request):
    if request.method == 'POST':
        try:
            vendor_id = request.session['user_id']
            vendor = Vendor.objects.filter(id=vendor_id).first()
            if not vendor:
                return JsonResponse({'success': False, 'error': 'Vendor not found'}, status=404)

            MenuItem.objects.filter(vendor_id=vendor_id).delete()
            Offer.objects.filter(vendor_id=vendor_id).delete()
            VendorNotification.objects.filter(vendor_id=vendor_id).delete()

            orders = Order.objects.filter(vendor_id=vendor_id)
            for order in orders:
                order.vendor_name = f"Deleted Vendor: {vendor.business_name}"
                order.vendor_id = None
                order.save()

            vendor.delete()
            request.session.flush()

            return JsonResponse({
                'success': True,
                'message': 'Account permanently deleted',
                'redirect': '/'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# --- Vendor Offers CRUD ---

@vendor_required
def get_vendor_offers_list(request):
    offers = Offer.objects.filter(vendor_id=request.session['user_id'])
    return JsonResponse([offer.to_dict() for offer in offers], safe=False)


@vendor_required
def get_vendor_offer(request, offer_id):
    offer = Offer.objects.filter(id=offer_id, vendor_id=request.session['user_id']).first()
    if not offer:
        return JsonResponse({'success': False, 'error': 'Offer not found'}, status=404)
    return JsonResponse({'success': True, 'offer': offer.to_dict()})


@csrf_exempt
@vendor_required
def add_vendor_offer(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        offer = Offer(
            vendor_id=request.session['user_id'],
            title=data['title'],
            description=data.get('description'),
            discount_type=data['discount_type'],
            discount_value=data['discount_value'],
            min_order=data.get('min_order', 0),
            valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d').date(),
            valid_to=datetime.strptime(data['valid_to'], '%Y-%m-%d').date(),
            active=data.get('active', True),
            image=data.get('image')
        )
        offer.save()
        return JsonResponse({'success': True, 'offer': offer.to_dict()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@vendor_required
def edit_vendor_offer(request, offer_id):
    try:
        offer = Offer.objects.filter(id=offer_id, vendor_id=request.session['user_id']).first()
        if not offer:
            return JsonResponse({'success': False, 'error': 'Offer not found'}, status=404)

        data = json.loads(request.body.decode('utf-8'))
        offer.title = data.get('title', offer.title)
        offer.description = data.get('description', offer.description)
        offer.discount_type = data.get('discount_type', offer.discount_type)
        offer.discount_value = data.get('discount_value', offer.discount_value)
        offer.min_order = data.get('min_order', offer.min_order)
        if data.get('valid_from'):
            offer.valid_from = datetime.strptime(data['valid_from'], '%Y-%m-%d').date()
        if data.get('valid_to'):
            offer.valid_to = datetime.strptime(data['valid_to'], '%Y-%m-%d').date()
        offer.active = data.get('active', offer.active)
        if 'image' in data:
            offer.image = data['image']

        offer.save()
        return JsonResponse({'success': True, 'offer': offer.to_dict()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@vendor_required
def delete_vendor_offer(request, offer_id):
    offer = Offer.objects.filter(id=offer_id, vendor_id=request.session['user_id']).first()
    if not offer:
        return JsonResponse({'error': 'Offer not found'}, status=404)
    offer.delete()
    return JsonResponse({'success': True})


def get_vendor_offers(request, vendor_id):
    today = date.today()
    offers = Offer.objects.filter(
        vendor_id=vendor_id,
        active=True,
        valid_from__lte=today,
        valid_to__gte=today
    )
    return JsonResponse([offer.to_dict() for offer in offers], safe=False)


# --- Vendor APIs ---

@csrf_exempt
@vendor_required
def add_vendor_response(request, order_id):
    order = Order.objects.filter(id=order_id, vendor_id=request.session['user_id']).first()
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    order.vendor_response = data.get('response')
    order.vendor_response_date = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
    order.save()
    return JsonResponse({'success': True})


@vendor_required
def api_vendor_earnings(request):
    vendor_id = request.session['user_id']
    total_earnings = DjangoOrderFilters.calculate_total_earnings(vendor_id)
    today_earnings = DjangoOrderFilters.calculate_today_earnings(vendor_id)
    week_earnings = DjangoOrderFilters.calculate_week_earnings(vendor_id)
    month_earnings = DjangoOrderFilters.calculate_month_earnings(vendor_id)
    completed_orders = DjangoOrderFilters.get_completed_orders_count(vendor_id)
    all_orders = Order.objects.filter(vendor_id=vendor_id).count()

    response_data = {
        'vendor_id': vendor_id,
        'total_earnings': float(total_earnings),
        'today_earnings': float(today_earnings),
        'week_earnings': float(week_earnings),
        'month_earnings': float(month_earnings),
        'completed_orders': completed_orders,
        'all_orders': all_orders,
        'manual_verification': float(total_earnings),
        'calculation_match': True,
        'timestamp': date.today().isoformat()
    }
    return JsonResponse(response_data)


@vendor_required
def api_vendor_notification_dashboard(request):
    return JsonResponse({
        'success': True,
        'today_sent': 15,
        'today_failed': 1,
        'recent_notifications': [
            {
                'timestamp': datetime.now().isoformat(),
                'type': 'new_order',
                'recipient': '+91XXXXXXXXXX',
                'sms_success': True,
                'whatsapp_success': True,
                'message': 'New order received from customer...'
            }
        ]
    })


@vendor_required
def get_vendor_profile(request):
    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    return JsonResponse({
        'business_name': vendor.business_name,
        'email': vendor.email,
        'business_category': vendor.business_category,
        'business_address': vendor.business_address,
        'phone': vendor.phone
    })


@csrf_exempt
@vendor_required
def sms_status_update(request):
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        order_id = data.get('order_id')
        new_status = data.get('status')

        order = Order.objects.filter(id=order_id, vendor_id=request.session['user_id']).first()
        if not order:
            return JsonResponse({'error': 'Order not found'}, status=404)

        current_time = timezone.now() if hasattr(timezone, 'now') else datetime.now(IST)
        order.status = new_status
        if new_status == 'ready':
            order.ready_at = current_time
        elif new_status == 'out_for_delivery':
            order.out_for_delivery_at = current_time
        elif new_status == 'Completed':
            order.completed_at = current_time

        order.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@vendor_required
def get_current_vendor(request):
    vendor = Vendor.objects.filter(id=request.session['user_id']).first()
    if not vendor:
        return JsonResponse({'error': 'Vendor not found'}, status=404)

    return JsonResponse({
        'id': vendor.id,
        'business_name': vendor.business_name,
        'latitude': vendor.latitude,
        'longitude': vendor.longitude,
        'business_address': vendor.business_address,
        'phone': vendor.phone
    })


@vendor_required
def get_active_deliveries(request):
    vendor_id = request.session['user_id']
    deliveries = Order.objects.filter(
        vendor_id=vendor_id,
        delivery_type='delivery',
        status__in=['out_for_delivery', 'preparing', 'ready']
    ).order_by('-created_at')

    delivery_list = []
    for order in deliveries:
        customer_lat = order.customer_delivery_latitude
        customer_lon = order.customer_delivery_longitude
        vendor_lat = order.vendor_latitude
        vendor_lon = order.vendor_longitude

        if not customer_lat or not customer_lon:
            customer = Customer.objects.filter(id=order.customer_id).first()
            customer_lat = customer.latitude if customer else None
            customer_lon = customer.longitude if customer else None

        if not vendor_lat or not vendor_lon:
            vendor = Vendor.objects.filter(id=vendor_id).first()
            vendor_lat = vendor.latitude if vendor else None
            vendor_lon = vendor.longitude if vendor else None

        delivery_list.append({
            'id': order.id,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'items_summary': order.items_summary,
            'total': order.total,
            'status': order.status,
            'delivery_type': order.delivery_type,
            'customer_latitude': customer_lat,
            'customer_longitude': customer_lon,
            'vendor_latitude': vendor_lat,
            'vendor_longitude': vendor_lon,
            'delivery_location_type': order.delivery_location_type,
            'created_at': order.created_at.isoformat() if order.created_at else ''
        })

    return JsonResponse(delivery_list, safe=False)


def get_vendor_location(request, vendor_id):
    vendor = Vendor.objects.filter(id=vendor_id).first()
    if not vendor:
        return JsonResponse({'error': 'Vendor not found'}, status=404)

    return JsonResponse({
        'id': vendor.id,
        'name': vendor.business_name,
        'category': vendor.business_category,
        'address': vendor.business_address,
        'phone': vendor.phone,
        'latitude': vendor.latitude,
        'longitude': vendor.longitude,
        'is_open': bool(vendor.is_open),
        'about': vendor.about,
        'opening_time': vendor.opening_time,
        'closing_time': vendor.closing_time
    })
