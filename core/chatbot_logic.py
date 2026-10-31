import json
import re
from django.http import JsonResponse
from django.db.models import Q, Avg
from core.models import Customer, Vendor, MenuItem, Order
from utils.distance import calculate_distance


def get_item_and_price(vendor_id, food_query):
    vendor = Vendor.objects.filter(id=vendor_id).first()
    if not vendor:
        return None, 0

    matched_item = MenuItem.objects.filter(
        vendor_id=vendor.id,
        name__icontains=food_query
    ).first()

    if not matched_item:
        return f"Chat Order: {food_query}", 0

    return matched_item.name, matched_item.price


def create_order_helper(request, user_id, customer, vendor_id, delivery_type, extra_fee=0, payment_type='cash'):
    try:
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not vendor:
            return None, "Vendor not found."

        food_query = request.session.get('chat_food_query', 'Food')
        item_name, base_price = get_item_and_price(vendor_id, food_query)
        total_price = base_price + extra_fee

        delivery_lat = customer.latitude
        delivery_lon = customer.longitude

        new_order = Order(
            customer_id=user_id,
            vendor_id=vendor.id,
            vendor_name=vendor.business_name,
            customer_name=customer.full_name,
            customer_phone=customer.phone,
            delivery_type=delivery_type,
            payment_type=payment_type,
            total=total_price,
            status='Pending' if payment_type == 'cash' else 'Pending Payment',
            customer_delivery_latitude=delivery_lat,
            customer_delivery_longitude=delivery_lon
        )

        if extra_fee > 0:
            new_order.items = json.dumps([{
                'name': item_name,
                'qty': 1,
                'price': base_price
            }, {
                'name': 'Delivery Fee',
                'qty': 1,
                'price': extra_fee
            }])
            new_order.items_summary = f"{item_name} x1, Delivery Fee"
        else:
            new_order.items = json.dumps([{
                'name': item_name,
                'qty': 1,
                'price': total_price
            }])
            new_order.items_summary = f"{item_name} x1"

        new_order.save()
        return new_order, None

    except Exception as e:
        print(f"Helper Error: {e}")
        return None, str(e)


def get_dish_variations(search_term):
    try:
        matches = MenuItem.objects.filter(
            name__icontains=search_term.lower()
        ).values_list('name', flat=True).distinct()
        return list(matches)
    except Exception as e:
        print(f"Error getting dish variations: {e}")
        return []


def perform_food_search(request, search_term, user_id, cust_lat, cust_lon):
    request.session['chat_food_query'] = search_term
    variations = get_dish_variations(search_term)

    do_disambiguation = False
    if len(variations) > 1:
        exact_match = next((name for name in variations if name.lower() == search_term.lower()), None)
        if not exact_match:
            do_disambiguation = True
        else:
            is_substring_of_others = any(exact_match.lower() in v.lower() and v.lower() != exact_match.lower() for v in variations)
            if is_substring_of_others:
                do_disambiguation = True

    if do_disambiguation:
        request.session['chat_state'] = 'WAITING_FOR_DISH_SELECTION'
        variations.sort(key=len)
        top_variations = variations[:5]
        reply = f"I found multiple items matching '{search_term}'.\nWhich one would you like?"
        buttons = [{'text': name, 'value': name} for name in top_variations]
        return JsonResponse({'reply': reply, 'buttons': buttons})

    vendors_by_profile = list(Vendor.objects.filter(
        Q(business_name__icontains=search_term) | Q(business_category__icontains=search_term)
    ))

    vendor_ids_by_menu = MenuItem.objects.filter(
        name__icontains=search_term
    ).values_list('vendor_id', flat=True).distinct()
    vendors_by_menu = list(Vendor.objects.filter(id__in=vendor_ids_by_menu))

    all_vendors = list({v.id: v for v in (vendors_by_profile + vendors_by_menu)}.values())

    if not all_vendors:
        reply = f"No shops found for '{search_term}'.\nPlease choose one of the following options to continue:"
        request.session['chat_state'] = 'MAIN_MENU'
        return JsonResponse({
            'reply': reply,
            'buttons': [
                {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                {'text': 'Order Something', 'value': 'Order Something'},
                {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                {'text': 'Chat History', 'value': 'Chat History'}
            ]
        })

    shop_list = []
    for v in all_vendors:
        dist = calculate_distance(cust_lat, cust_lon, v.latitude, v.longitude)
        avg_rating = Order.objects.filter(
            vendor=v,
            review_rating__isnull=False,
            status='Completed'
        ).aggregate(avg=Avg('review_rating'))['avg'] or 0.0

        shop_list.append({
            'id': v.id,
            'name': v.business_name,
            'rating': round(avg_rating, 1) if avg_rating > 0 else 'New',
            'distance': dist,
            'phone': v.phone
        })

    shop_list.sort(key=lambda x: x['distance'])
    request.session['chat_shops'] = shop_list
    request.session['chat_state'] = 'WAITING_FOR_SHOP'

    reply = f"Here are the available shops for '{search_term}':\nPlease tell me which shop you want to book from."
    shop_buttons = []
    for shop in shop_list[:5]:
        rating = shop['rating']
        shop_buttons.append({'text': f"{shop['name']} ⭐{rating} ({shop['distance']}km)", 'value': shop['name']})

    return JsonResponse({'reply': reply, 'buttons': shop_buttons})


def chat_logic(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    user_msg = data.get('message', '').strip()
    user_id = request.session.get('user_id')

    customer = Customer.objects.filter(id=user_id).first()
    cust_lat = getattr(customer, 'current_latitude', None) or getattr(customer, 'latitude', None) or getattr(customer, 'home_latitude', None)
    cust_lon = getattr(customer, 'current_longitude', None) or getattr(customer, 'longitude', None) or getattr(customer, 'home_longitude', None)

    chat_state = request.session.get('chat_state', 'MAIN_MENU')

    # Global Reset
    if user_msg.lower() in ['hi', 'hello', 'start', 'restart', 'menu']:
        chat_state = 'MAIN_MENU'
        request.session['chat_state'] = chat_state
        return JsonResponse({
            'reply': "Hello 👋 Welcome to LocalConnect.\nHow can I help you today?",
            'buttons': [
                {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                {'text': 'Order Something', 'value': 'Order Something'},
                {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                {'text': 'Chat History', 'value': 'Chat History'}
            ]
        })

    if chat_state == 'MAIN_MENU':
        msg_lower = user_msg.lower()

        if msg_lower == 'order something':
            reply = "What would you like to order today? 🛍️\nPlease type the item name."
            request.session['chat_state'] = 'WAITING_FOR_FOOD'
            return JsonResponse({'reply': reply})

        if msg_lower.startswith('order '):
            search_from_cmd = user_msg[6:].strip()
            if len(search_from_cmd) > 2 and search_from_cmd.lower() not in ['food', 'something']:
                return perform_food_search(request, search_from_cmd, user_id, cust_lat, cust_lon)

        if user_msg == 'CMD_AGENT_CHAT_ENDED':
            reply = "Thank you for using LocalConnect ChatAgent with us. 🙏\nHow would you rate your experience?"
            buttons = [
                {'text': '⭐⭐⭐⭐⭐', 'value': 'RATE_AGENT: 5'},
                {'text': '⭐⭐⭐⭐', 'value': 'RATE_AGENT: 4'},
                {'text': '⭐⭐⭐', 'value': 'RATE_AGENT: 3'},
                {'text': '⭐⭐', 'value': 'RATE_AGENT: 2'},
                {'text': '⭐', 'value': 'RATE_AGENT: 1'}
            ]
            return JsonResponse({'reply': reply, 'buttons': buttons})

        if user_msg.startswith('RATE_AGENT:'):
            reply = "Thank you for your valuable feedback! 💚\nLet us know if you need anything else."
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

        if user_msg == '1' or 'about' in msg_lower:
            reply = "LocalConnect is a platform that helps customers discover nearby local businesses, food shops, and service providers in their area.\nIt connects customers directly with trusted local vendors through a simple and fast system."
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

        elif user_msg == '2' or 'why' in msg_lower:
            reply = "LocalConnect is built to support and protect local vendors from vanishing in the digital world.\nWe help small food shops, service providers, and local businesses get visibility, customers, and orders without expensive platforms.\nUsing LocalConnect means supporting local livelihoods, faster service, and trusted nearby vendors."
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

        elif user_msg == '3' or 'order' in msg_lower:
            reply = "What would you like to order today? 🛍️\nPlease type the item name."
            request.session['chat_state'] = 'WAITING_FOR_FOOD'
            return JsonResponse({'reply': reply})

        elif user_msg == '4' or any(k in msg_lower for k in ['agent', 'help', 'human', 'support']):
            request.session['chat_state'] = 'MAIN_MENU'
            return JsonResponse({
                "reply": "Connecting you to a live support agent 👨💼…",
                "handoff": True
            })

        elif user_msg == '5' or 'history' in msg_lower:
            last_orders = Order.objects.filter(customer_id=user_id).order_by('-id')[:5]
            if not last_orders:
                reply = "You have no previous chat/order history."
            else:
                reply = "📜 **Your Recent History:**\n"
                for o in last_orders:
                    reply += f"- {o.items_summary} ({o.status} - ₹{o.total})\n"

            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

        else:
            reply = "Please choose one of the following options to continue:"
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

    elif chat_state == 'WAITING_FOR_FOOD':
        return perform_food_search(request, user_msg.lower(), user_id, cust_lat, cust_lon)

    elif chat_state == 'WAITING_FOR_DISH_SELECTION':
        return perform_food_search(request, user_msg, user_id, cust_lat, cust_lon)

    elif chat_state == 'WAITING_FOR_SHOP':
        selection = None
        shops = request.session.get('chat_shops', [])

        if user_msg.lower() in ['yes', 'book for me', 'ok', 'sure', 'book']:
            if shops:
                selection = shops[0]

        if not selection:
            for shop in shops:
                if shop['name'].lower() in user_msg.lower():
                    selection = shop
                    break

        if selection:
            request.session['chat_selected_shop_id'] = selection['id']
            reply = f"You selected {selection['name']}.\nHow would you like to receive your order?"
            request.session['chat_state'] = 'WAITING_FOR_DELIVERY_TYPE'
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': '🛵 Delivery', 'value': 'Delivery'},
                    {'text': '🥡 Takeaway', 'value': 'Takeaway'}
                ]
            })
        else:
            reply = "Please choose one of the following options to continue:"
            request.session['chat_state'] = 'MAIN_MENU'
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
            })

    elif chat_state == 'WAITING_FOR_DELIVERY_TYPE':
        msg_lower = user_msg.lower()
        vendor_id = request.session.get('chat_selected_shop_id')
        if not vendor_id:
            request.session['chat_state'] = 'MAIN_MENU'
            return JsonResponse({'reply': "Session expired. Please start over."})

        if any(k in msg_lower for k in ['take', 'pickup', 'away']):
            food_query = request.session.get('chat_food_query', 'Food')
            item_name, price = get_item_and_price(vendor_id, food_query)

            request.session['chat_delivery_type'] = 'takeaway'
            request.session['chat_delivery_fee'] = 0
            request.session['chat_total_price'] = price

            if price > 200:
                reply = f"Total: ₹{price} (Takeaway).\n⚠️ Orders above ₹200 require Online Payment."
                buttons = [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
            else:
                reply = f"Total: ₹{price} (Takeaway).\nSelect Payment Method:"
                buttons = [
                    {'text': '💵 Cash on Pickup', 'value': 'Cash on Pickup'},
                    {'text': '💳 Online Payment', 'value': 'Online Payment'}
                ]

            request.session['chat_state'] = 'WAITING_FOR_PAYMENT_METHOD'
            return JsonResponse({'reply': reply, 'buttons': buttons})

        elif 'deliver' in msg_lower:
            reply = "Where would you like the delivery?\n(Delivery Fee: ₹30)"
            request.session['chat_state'] = 'WAITING_FOR_DELIVERY_LOCATION'
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': '🏠 Home Location', 'value': 'Home Location'},
                    {'text': '📍 Current Location', 'value': 'Current Location'}
                ]
            })
        else:
            return JsonResponse({
                'reply': "Please select Delivery or Takeaway.",
                'buttons': [
                    {'text': '🛵 Delivery', 'value': 'Delivery'},
                    {'text': '🥡 Takeaway', 'value': 'Takeaway'}
                ]
            })

    elif chat_state == 'WAITING_FOR_DELIVERY_LOCATION':
        vendor_id = request.session.get('chat_selected_shop_id')
        food_query = request.session.get('chat_food_query', 'Food')
        item_name, price = get_item_and_price(vendor_id, food_query)
        total = price + 30

        request.session['chat_delivery_type'] = 'delivery'
        request.session['chat_delivery_fee'] = 30
        request.session['chat_total_price'] = total

        if total > 200:
            reply = f"Total: ₹{total} (Delivery + Fee).\n⚠️ Orders above ₹200 require Online Payment."
            buttons = [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
        else:
            reply = f"Total: ₹{total} (Delivery + Fee).\nSelect Payment Method:"
            buttons = [
                {'text': '💵 Cash on Delivery', 'value': 'Cash on Delivery'},
                {'text': '💳 Online Payment', 'value': 'Online Payment'}
            ]

        request.session['chat_state'] = 'WAITING_FOR_PAYMENT_METHOD'
        return JsonResponse({'reply': reply, 'buttons': buttons})

    elif chat_state == 'WAITING_FOR_PAYMENT_METHOD':
        msg_lower = user_msg.lower()
        vendor_id = request.session.get('chat_selected_shop_id')
        delivery_type = request.session.get('chat_delivery_type')
        fee = request.session.get('chat_delivery_fee', 0)
        total = request.session.get('chat_total_price', 0)

        payment_type = None
        if 'online' in msg_lower or 'pay now' in msg_lower:
            payment_type = 'online'
        elif any(k in msg_lower for k in ['cash', 'cod', 'pickup']):
            if total > 200:
                reply = "⚠️ Order > ₹200 requires Online Payment. Please select Online Payment."
                return JsonResponse({
                    'reply': reply,
                    'buttons': [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
                })
            payment_type = 'cash'

        if payment_type:
            order, error = create_order_helper(request, user_id, customer, vendor_id, delivery_type, fee, payment_type)
            if order:
                if payment_type == 'online':
                    reply = "Initiating secure payment via Razorpay... Please complete the payment in the popup window."
                    request.session['chat_state'] = 'MAIN_MENU'
                    return JsonResponse({
                        'reply': reply,
                        'buttons': [
                            {'text': 'Order Something', 'value': 'Order Something'},
                            {'text': 'Chat History', 'value': 'Chat History'}
                        ],
                        'payment_required': True,
                        'order_id': order.id,
                        'amount': order.total
                    })
                else:
                    reply = f"✅ Order Booked Successfully.\nTotal: ₹{total}. You can pay cash upon {'pickup' if delivery_type=='takeaway' else 'delivery'}."
            else:
                reply = "Error booking order. Please try again."

            request.session['chat_state'] = 'MAIN_MENU'
            return JsonResponse({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'}
                ]
            })
        else:
            reply = "Please select a valid payment method."
            if total > 200:
                buttons = [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
            else:
                if delivery_type == 'takeaway':
                    buttons = [
                        {'text': '💵 Cash on Pickup', 'value': 'Cash on Pickup'},
                        {'text': '💳 Online Payment', 'value': 'Online Payment'}
                    ]
                else:
                    buttons = [
                        {'text': '💵 Cash on Delivery', 'value': 'Cash on Delivery'},
                        {'text': '💳 Online Payment', 'value': 'Online Payment'}
                    ]
            return JsonResponse({'reply': reply, 'buttons': buttons})

    request.session['chat_state'] = 'MAIN_MENU'
    return JsonResponse({
        'reply': "Please choose one of the following options to continue:",
        'buttons': [
            {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
            {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
            {'text': 'Order Something', 'value': 'Order Something'},
            {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
            {'text': 'Chat History', 'value': 'Chat History'}
        ]
    })
