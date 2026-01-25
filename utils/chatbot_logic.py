from flask import request, session, jsonify
from models.models import db, Customer, Vendor, MenuItem, Order
from utils.distance import calculate_distance
from sqlalchemy import func, or_
import re
import json

def get_item_and_price(vendor_id, food_query):
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return None, 0
        
    matched_item = MenuItem.query.filter(
        MenuItem.vendor_id == vendor.id,
        func.lower(MenuItem.name).contains(food_query)
    ).first()
    
    if not matched_item:
        return f"Chat Order: {food_query}", 0
    
    return matched_item.name, matched_item.price

def create_order_helper(user_id, customer, vendor_id, delivery_type, extra_fee=0, payment_type='cash'):
    try:
        vendor = Vendor.query.get(vendor_id)
        if not vendor:
            return None, "Vendor not found."

        food_query = session.get('chat_food_query', 'Food')
        item_name, base_price = get_item_and_price(vendor_id, food_query)

        total_price = base_price + extra_fee
        
        # Determine Delivery Coords (default to customer profile)
        delivery_lat = customer.latitude
        delivery_lon = customer.longitude
        
        # If Current Location was chosen, we assume the frontend/app updated the customer 
        # profile or we sent it - for now we use what is in DB for the customer.

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
            items=json.dumps([{
                'name': item_name,
                'qty': 1,
                'price': total_price
            }]),
            customer_delivery_latitude=delivery_lat,
            customer_delivery_longitude=delivery_lon
        )
        
        # Summary
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
            new_order.items_summary = f"{item_name} x1"
        
        db.session.add(new_order)
        db.session.commit()
        
        return new_order, None

    except Exception as e:
        print(f"Helper Error: {e}")
        return None, str(e)

def get_dish_variations(search_term):
    """
    Find distinct dish names matching the search term.
    Returns a list of unique dish names.
    """
    try:
        # Search for unique dish names containing the search term
        matches = db.session.query(MenuItem.name).filter(
            func.lower(MenuItem.name).contains(search_term.lower())
        ).distinct().all()
        
        # Extract names from tuples
        unique_names = [m[0] for m in matches]
        
        # Filter to remove very similar variations if needed, but for now exact logic
        return unique_names
    except Exception as e:
        print(f"Error getting dish variations: {e}")
        return []

def perform_food_search(search_term, user_id, cust_lat, cust_lon):
    """
    Reusable helper to search for food and return chat response JSON.
    Used by both 'Order <Food>' command and manual entry.
    """
    session['chat_food_query'] = search_term
    
    # Check for dish variations first
    variations = get_dish_variations(search_term)
    
    # Determine if we should disambiguate
    do_disambiguation = False
    
    if len(variations) > 1:
        # Check if search_term matches exactly one of the variations
        exact_match = next((name for name in variations if name.lower() == search_term.lower()), None)
        
        if not exact_match:
            # No exact match, so definitely disambiguate
            do_disambiguation = True
        else:
            # Exact match exists. 
            # Check if this exact match is a substring of any OTHER variation
            # e.g. "Briyani" is in "Chicken Briyani" -> Disambiguate
            is_substring_of_others = any(exact_match.lower() in v.lower() and v.lower() != exact_match.lower() for v in variations)
            
            if is_substring_of_others:
                do_disambiguation = True
    
    if do_disambiguation:
        session['chat_state'] = 'WAITING_FOR_DISH_SELECTION'
        
        # Sort variations by length (shortest/generic first)
        variations.sort(key=len)
        
        # Take top 5 to avoid clutter
        top_variations = variations[:5]
        
        reply = f"I found multiple items matching '{search_term}'.\nWhich one would you like?"
        buttons = [{'text': name, 'value': name} for name in top_variations]
        
        return jsonify({'reply': reply, 'buttons': buttons})

    # If 1 match or no matches, or valid exact match that isn't a substring, proceed with standard vendor search
    
    vendors_by_profile = Vendor.query.filter(
        or_(
            func.lower(Vendor.business_name).contains(search_term),
            func.lower(Vendor.business_category).contains(search_term)
        )
    ).all()
    
    vendors_by_menu = db.session.query(Vendor).join(MenuItem).filter(
        func.lower(MenuItem.name).contains(search_term)
    ).distinct().all()
    
    all_vendors = list(set(vendors_by_profile + vendors_by_menu))
    
    if not all_vendors:
            reply = f"No shops found for '{search_term}'.\nPlease choose one of the following options to continue:"
            session['chat_state'] = 'MAIN_MENU'
            return jsonify({
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
        avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).scalar() or 0.0
        
        shop_list.append({
            'id': v.id,
            'name': v.business_name,
            'rating': round(avg_rating, 1) if avg_rating > 0 else 'New',
            'distance': dist,
            'phone': v.phone
        })
        
    shop_list.sort(key=lambda x: x['distance'])
    session['chat_shops'] = shop_list
    session['chat_state'] = 'WAITING_FOR_SHOP'
    
    reply = f"Here are the available shops for '{search_term}':\nPlease tell me which shop you want to book from."
    shop_buttons = []
    for i, shop in enumerate(shop_list[:5], 1):
            rating = shop['rating']
            shop_buttons.append({'text': f"{shop['name']} ⭐{rating} ({shop['distance']}km)", 'value': shop['name']})
    
    return jsonify({'reply': reply, 'buttons': shop_buttons})

def chat_logic():
    data = request.json
    user_msg = data.get('message', '').strip()
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    cust_lat = getattr(customer, 'current_latitude', None) or getattr(customer, 'latitude', None) or getattr(customer, 'home_latitude', None)
    cust_lon = getattr(customer, 'current_longitude', None) or getattr(customer, 'longitude', None) or getattr(customer, 'home_longitude', None)
    
    chat_state = session.get('chat_state', 'MAIN_MENU')
    
    # Global Reset
    if user_msg.lower() in ['hi', 'hello', 'start', 'restart', 'menu']:
        chat_state = 'MAIN_MENU'
        session['chat_state'] = chat_state
        return jsonify({
            'reply': "Hello 👋 Welcome to LocalConnect.\nHow can I help you today?",
            'buttons': [
                {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
                {'text': 'Order Something', 'value': 'Order Something'},
                {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                {'text': 'Chat History', 'value': 'Chat History'}
            ]
        })

    reply = ""
    
    if chat_state == 'MAIN_MENU':
        msg_lower = user_msg.lower()
        
        # --- Explicit Handler for Order Something ---
        if msg_lower == 'order something':
             reply = "What would you like to order today? 🛍️\nPlease type the item name."
             session['chat_state'] = 'WAITING_FOR_FOOD'
             return jsonify({'reply': reply})
        # --------------------------------------------

        # --- NEW: Check for "Order <Food>" Pattern ---
        if msg_lower.startswith('order '):
            search_from_cmd = user_msg[6:].strip() # Remove 'order '
            if len(search_from_cmd) > 2 and search_from_cmd.lower() not in ['food', 'something']:
                 # Direct jump to search
                 return perform_food_search(search_from_cmd, user_id, cust_lat, cust_lon)
        # ---------------------------------------------

        # --- NEW: Agent Chat End / Rating Flow ---
        if user_msg == 'CMD_AGENT_CHAT_ENDED':
             reply = "Thank you for using LocalConnect ChatAgent with us. 🙏\nHow would you rate your experience?"
             buttons = [
                 {'text': '⭐⭐⭐⭐⭐', 'value': 'RATE_AGENT: 5'},
                 {'text': '⭐⭐⭐⭐', 'value': 'RATE_AGENT: 4'},
                 {'text': '⭐⭐⭐', 'value': 'RATE_AGENT: 3'},
                 {'text': '⭐⭐', 'value': 'RATE_AGENT: 2'},
                 {'text': '⭐', 'value': 'RATE_AGENT: 1'}
             ]
             return jsonify({'reply': reply, 'buttons': buttons})

        if user_msg.startswith('RATE_AGENT:'):
             reply = "Thank you for your valuable feedback! 💚\nLet us know if you need anything else."
             return jsonify({
                'reply': reply,
                'buttons': [
                    {'text': 'Order Something', 'value': 'Order Something'},
                    {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
                    {'text': 'Chat History', 'value': 'Chat History'}
                ]
             })
        # ---------------------------------------------
        
        if user_msg == '1' or 'about' in msg_lower:
            reply = "LocalConnect is a platform that helps customers discover nearby local businesses, food shops, and service providers in their area.\nIt connects customers directly with trusted local vendors through a simple and fast system."
            return jsonify({
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
            return jsonify({
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
            session['chat_state'] = 'WAITING_FOR_FOOD'
            return jsonify({'reply': reply})
            
        elif user_msg == '4' or 'agent' in msg_lower or 'help' in msg_lower or 'human' in msg_lower or 'support' in msg_lower:
            session['chat_state'] = 'MAIN_MENU'
            return jsonify({
                "reply": "Connecting you to a live support agent 👨💼…",
                "handoff": True
            })
            
        elif user_msg == '5' or 'history' in msg_lower:
            last_orders = Order.query.filter_by(customer_id=user_id).order_by(Order.id.desc()).limit(5).all()
            if not last_orders:
                reply = "You have no previous chat/order history."
            else:
                reply = "📜 **Your Recent History:**\n"
                for o in last_orders:
                    reply += f"- {o.items_summary} ({o.status} - ₹{o.total})\n"
            
            return jsonify({
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
            return jsonify({
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
        search_term = user_msg.lower()
        # Use helper
        return perform_food_search(search_term, user_id, cust_lat, cust_lon)
    
    elif chat_state == 'WAITING_FOR_DISH_SELECTION':
        # User selected a specific dish variation
        selected_dish = user_msg
        # Use helper
        return perform_food_search(selected_dish, user_id, cust_lat, cust_lon)

    elif chat_state == 'WAITING_FOR_SHOP':
        selection = None
        shops = session.get('chat_shops', [])
        
        if user_msg.lower() in ['yes', 'book for me', 'ok', 'sure', 'book']:
            if shops:
                selection = shops[0]
        
        if not selection:
            for shop in shops:
                if shop['name'].lower() in user_msg.lower():
                    selection = shop
                    break
        
        if selection:
            session['chat_selected_shop_id'] = selection['id']
            reply = f"You selected {selection['name']}.\nHow would you like to receive your order?"
            session['chat_state'] = 'WAITING_FOR_DELIVERY_TYPE'
            return jsonify({
                'reply': reply,
                'buttons': [
                    {'text': '🛵 Delivery', 'value': 'Delivery'},
                    {'text': '🥡 Takeaway', 'value': 'Takeaway'}
                ]
            })
        else:
            reply = "Please choose one of the following options to continue:"
            session['chat_state'] = 'MAIN_MENU'
            return jsonify({
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
        vendor_id = session.get('chat_selected_shop_id')
        if not vendor_id:
             session['chat_state'] = 'MAIN_MENU'
             return jsonify({'reply': "Session expired. Please start over."})
             
        if 'take' in msg_lower or 'pickup' in msg_lower or 'away' in msg_lower:
            # TAKEAWAY: FEE = 0
            # Calculate Total
            food_query = session.get('chat_food_query', 'Food')
            item_name, price = get_item_and_price(vendor_id, food_query)
            
            session['chat_delivery_type'] = 'takeaway'
            session['chat_delivery_fee'] = 0
            session['chat_total_price'] = price
            
            # Payment Check Flow
            if price > 200:
                 reply = f"Total: ₹{price} (Takeaway).\n⚠️ Orders above ₹200 require Online Payment."
                 buttons = [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
            else:
                 reply = f"Total: ₹{price} (Takeaway).\nSelect Payment Method:"
                 buttons = [
                     {'text': '💵 Cash on Pickup', 'value': 'Cash on Pickup'},
                     {'text': '💳 Online Payment', 'value': 'Online Payment'}
                 ]
            
            session['chat_state'] = 'WAITING_FOR_PAYMENT_METHOD'
            return jsonify({'reply': reply, 'buttons': buttons})

        elif 'deliver' in msg_lower:
            # DELIVERY: Ask for Location (Fee not finalized until next step if code structure changed, 
            # but we know it's 30. We'll set it here tentatively?)
            # Actually, standard flow asks Location next.
            reply = "Where would you like the delivery?\n(Delivery Fee: ₹30)"
            session['chat_state'] = 'WAITING_FOR_DELIVERY_LOCATION'
            return jsonify({
                'reply': reply,
                'buttons': [
                    {'text': '🏠 Home Location', 'value': 'Home Location'},
                    {'text': '📍 Current Location', 'value': 'Current Location'}
                ]
            })
        else:
            return jsonify({
                'reply': "Please select Delivery or Takeaway.",
                'buttons': [
                    {'text': '🛵 Delivery', 'value': 'Delivery'},
                    {'text': '🥡 Takeaway', 'value': 'Takeaway'}
                ]
            })

    elif chat_state == 'WAITING_FOR_DELIVERY_LOCATION':
        msg_lower = user_msg.lower()
        vendor_id = session.get('chat_selected_shop_id')
        
        # Calculate Total with Fee
        food_query = session.get('chat_food_query', 'Food')
        item_name, price = get_item_and_price(vendor_id, food_query)
        total = price + 30
        
        session['chat_delivery_type'] = 'delivery'
        session['chat_delivery_fee'] = 30
        session['chat_total_price'] = total
        
        # Payment Check
        if total > 200:
             reply = f"Total: ₹{total} (Delivery + Fee).\n⚠️ Orders above ₹200 require Online Payment."
             buttons = [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
        else:
             reply = f"Total: ₹{total} (Delivery + Fee).\nSelect Payment Method:"
             buttons = [
                 {'text': '💵 Cash on Delivery', 'value': 'Cash on Delivery'},
                 {'text': '💳 Online Payment', 'value': 'Online Payment'}
             ]
        
        session['chat_state'] = 'WAITING_FOR_PAYMENT_METHOD'
        return jsonify({'reply': reply, 'buttons': buttons})

    elif chat_state == 'WAITING_FOR_PAYMENT_METHOD':
        msg_lower = user_msg.lower()
        vendor_id = session.get('chat_selected_shop_id')
        delivery_type = session.get('chat_delivery_type')
        fee = session.get('chat_delivery_fee', 0)
        total = session.get('chat_total_price', 0)
        
        payment_type = None
        
        if 'online' in msg_lower or 'pay now' in msg_lower:
            payment_type = 'online'
        elif 'cash' in msg_lower or 'cod' in msg_lower or 'pickup' in msg_lower:
            if total > 200:
                # Security Check
                reply = "⚠️ Order > ₹200 requires Online Payment. Please select Online Payment."
                return jsonify({
                    'reply': reply, 
                    'buttons': [{'text': '💳 Online Payment', 'value': 'Online Payment'}]
                })
            payment_type = 'cash'
        
        if payment_type:
            # Create Order
            order, error = create_order_helper(user_id, customer, vendor_id, delivery_type, fee, payment_type)
            
            if order:
                if payment_type == 'online':
                    reply = "Initiating secure payment via Razorpay... Please complete the payment in the popup window."
                    session['chat_state'] = 'MAIN_MENU'
                    return jsonify({
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
            
            session['chat_state'] = 'MAIN_MENU'
            return jsonify({
                'reply': reply,
                'buttons': [
                    {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
                    {'text': 'Order Something', 'value': 'Order Something'}
                ]
            })
        else:
             # Invalid
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
             return jsonify({'reply': reply, 'buttons': buttons})

    # Fallback
    session['chat_state'] = 'MAIN_MENU'
    return jsonify({
        'reply': "Please choose one of the following options to continue:",
        'buttons': [
            {'text': 'About LocalConnect', 'value': 'About LocalConnect'},
            {'text': 'Why use LocalConnect', 'value': 'Why use LocalConnect'},
            {'text': 'Order Something', 'value': 'Order Something'},
            {'text': 'Talk to Agent', 'value': 'Talk to Agent'},
            {'text': 'Chat History', 'value': 'Chat History'}
        ]
    })
