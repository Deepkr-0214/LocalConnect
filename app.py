from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models.models import db, Customer, Vendor, Order, MenuItem
import os
from datetime import datetime
import json
from functools import wraps
import razorpay
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "instance", "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'customer':
            flash('Access denied. Customer login required.', 'error')
            return redirect(url_for('sign_in'))
        return f(*args, **kwargs)
    return decorated_function

def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'vendor':
            flash('Access denied. Vendor login required.', 'error')
            return redirect(url_for('sign_in'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/signin', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        
        if role == 'customer':
            # Check if username is email or phone
            customer = Customer.query.filter(
                (Customer.email == username) | (Customer.phone == username)
            ).first()
            
            if customer and customer.check_password(password):
                session['user_id'] = customer.id
                session['user_name'] = customer.full_name
                session['user_email'] = customer.email
                session['user_role'] = 'customer'
                flash('Login successful!', 'success')
                return redirect(url_for('customer_dashboard'))
            else:
                flash('Invalid credentials', 'error')
                return redirect(url_for('sign_in'))
                
        elif role == 'vendor':
            # For vendor, use email for login
            vendor = Vendor.query.filter_by(email=username).first()
            
            if vendor and vendor.check_password(password):
                session['user_id'] = vendor.id
                session['user_name'] = vendor.business_name
                session['user_email'] = vendor.email
                session['user_role'] = 'vendor'
                flash('Login successful!', 'success')
                return redirect(url_for('vendor_dashboard'))
            else:
                flash('Invalid credentials', 'error')
                return redirect(url_for('sign_in'))
    
    return render_template('sign_in.html')

@app.route('/customer/dashboard')
@customer_required
def customer_dashboard():
    user_id = session.get('user_id')
    return render_template('customer/base.html', user_name=session.get('user_name'), user_id=user_id)

@app.route('/customer/food-restaurants')
@customer_required
def food_restaurants():
    from sqlalchemy import func
    user_id = session.get('user_id')
    vendors = Vendor.query.all()
    vendors_data = []
    
    for v in vendors:
        # Get min and max prices from vendor's menu
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 100
        max_price = int(price_query.max_price) if price_query.max_price else 300
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '🏪',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price
        })
    
    return render_template('customer/food&rest.html', user_name=session.get('user_name'), user_id=user_id, vendors=vendors_data)

@app.route('/customer/orders')
@customer_required
def customer_orders():
    user_id = session.get('user_id')
    orders_query = Order.query.filter_by(customer_id=user_id).order_by(Order.created_at.desc()).all()
    orders = [{
        'id': o.id,
        'vendor_name': o.vendor_name,
        'items': o.items,
        'delivery_type': o.delivery_type,
        'payment_type': o.payment_type,
        'total': o.total,
        'status': o.status,
        'created_at': o.created_at.isoformat(),
        'review_rating': o.review_rating,
        'review_comment': o.review_comment
    } for o in orders_query]
    return render_template('customer/orders.html', user_name=session.get('user_name'), user_id=user_id, orders=orders, orders_query=orders_query)

@app.route('/customer/profile')
@customer_required
def customer_profile():
    user_id = session.get('user_id')
    customer = Customer.query.get(user_id)
    return render_template('customer/profile.html', user_name=session.get('user_name'), customer=customer, user_id=user_id)

@app.route('/customer/vendor/<int:vendor_id>')
@customer_required
def vendor_details(vendor_id):
    user_id = session.get('user_id')
    vendor = Vendor.query.get_or_404(vendor_id)
    return render_template('customer/viewdet.html', vendor_id=vendor_id, vendor=vendor, user_name=session.get('user_name'), user_id=user_id)

@app.route('/api/vendor/<int:vendor_id>/menu')
def get_vendor_menu(vendor_id):
    items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'sub_name': item.sub_name,
        'category': item.category,
        'price': item.price,
        'is_available': item.is_available,
        'image_file': item.image_file
    } for item in items])

@app.route('/customer/signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('customer_signup'))

        # Check if email already exists
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            flash('Email already registered', 'error')
            return redirect(url_for('customer_signup'))

        new_customer = Customer(full_name=full_name, email=email, phone=phone)
        new_customer.set_password(password)
        db.session.add(new_customer)
        db.session.commit()

        session['user_id'] = new_customer.id
        session['user_name'] = new_customer.full_name
        session['user_email'] = new_customer.email
        session['user_role'] = 'customer'
        flash('Signup successful!', 'success')
        return redirect(url_for('customer_dashboard'))

    return render_template('customer/sign_up.html')
            
@app.route('/api/orders', methods=['POST'])
@customer_required
def create_order():
    try:
        data = request.json
        customer = Customer.query.get(session['user_id'])
        vendor = Vendor.query.get(data['vendor_id'])
        
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
        
        order = Order(
            customer_id=session['user_id'],
            vendor_id=vendor.id,
            vendor_name=vendor.business_name,
            customer_name=customer.full_name,
            customer_phone=customer.phone,
            delivery_type=data['deliveryType'],
            payment_type=data['paymentType'],
            order_type=data['deliveryType'],
            total=data['total'],
            status='Pending' if data['paymentType'] != 'online' else 'Payment Pending'
        )
        order.set_items(data['items'])
        db.session.add(order)
        db.session.commit()
        print(f"Order created: ID={order.id}, Customer={customer.full_name}, Vendor={vendor.business_name}")
        return jsonify({'success': True, 'order_id': order.id})
    except Exception as e:
        print(f"Error creating order: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@customer_required
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
    if order and order.status == 'Pending':
        order.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Cannot cancel'}), 400

@app.route('/api/payment/create', methods=['POST'])
@customer_required
def create_payment():
    try:
        data = request.json
        order_id = data.get('order_id')
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
            
        # Amount in paise (multiply by 100)
        amount = int(order.total * 100)
        
        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        order.razorpay_order_id = razorpay_order['id']
        db.session.commit()
        
        return jsonify({
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'amount': amount,
            'customer_name': order.customer_name,
            'customer_email': session.get('user_email', ''),
            'customer_phone': order.customer_phone
        })
    except Exception as e:
        print(f"Error creating Razorpay order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/verify', methods=['POST'])
@customer_required
def verify_payment():
    try:
        data = request.json
        order_id = data.get('order_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            order = Order.query.filter_by(id=order_id, razorpay_order_id=razorpay_order_id).first()
            if order:
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.status = 'Pending' # Now that payment is done, it's pending for vendor action
                db.session.commit()
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Order not found'}), 404
        except Exception as sig_error:
            print(f"Signature verification failed: {sig_error}")
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400
            
    except Exception as e:
        print(f"Error verifying payment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@customer_required
def delete_order(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
    if order and (order.status == 'cancelled' or order.status == 'delivered'):
        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Cannot delete'}), 400

@app.route('/api/orders/<int:order_id>/review', methods=['POST'])
@customer_required
def add_review(order_id):
    data = request.json
    order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
    if order:
        order.review_rating = data['rating']
        order.review_comment = data['comment']
        order.review_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Order not found'}), 404

@app.route('/api/profile', methods=['POST'])
@customer_required
def update_profile():
    data = request.json
    customer = Customer.query.get(session['user_id'])
    if customer:
        customer.address = data.get('address')
        customer.city = data.get('city')
        customer.state = data.get('state')
        customer.pincode = data.get('pincode')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Customer not found'}), 404

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    from datetime import date
    from sqlalchemy import func
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(5).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    today = date.today()
    todays_orders = Order.query.filter(Order.vendor_id==vendor_id, func.date(Order.created_at)==today).count()
    todays_earnings = db.session.query(func.sum(Order.total)).filter(Order.vendor_id==vendor_id, func.date(Order.created_at)==today, Order.status!='Rejected').scalar() or 0
    pending_orders = unread_count
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(Order.vendor_id==vendor_id, Order.review_rating!=None).scalar() or 0
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).limit(5).all()
    
    return render_template('vendor/vendor_dashboard.html', orders=orders, vendor_profile=vendor, unread_count=unread_count,
                         todays_orders=todays_orders, todays_earnings=todays_earnings, pending_orders=pending_orders,
                         avg_rating=avg_rating, menu_items=menu_items)
@app.route('/vendor/orders')
@vendor_required
def vendor_orders():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    return render_template('vendor/orders.html', orders=orders, vendor_profile=vendor, unread_count=unread_count)

@app.route('/vendor/orders/<int:order_id>/status', methods=['POST'])
@vendor_required
def update_order_status(order_id):
    order = Order.query.filter_by(id=order_id, vendor_id=session['user_id']).first()
    if not order:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.json
    order.status = data['status']
    if data.get('rejection_reason'):
        order.rejection_reason = data['rejection_reason']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/vendor/menu')
@vendor_required
def vendor_menu():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    return render_template('vendor/menu.html', menu_items=menu_items, items=menu_items, vendor_profile=vendor, unread_count=unread_count)

@app.route('/vendor/menu/add', methods=['POST'])
@vendor_required
def add_menu_item():
    import os
    import base64
    from datetime import datetime
    
    data = request.json
    image_file = 'default.jpg'
    
    # Handle base64 image
    if data.get('image_file') and data['image_file'].startswith('data:image'):
        try:
            # Extract base64 data
            header, image_data = data['image_file'].split(',', 1)
            image_bytes = base64.b64decode(image_data)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ext = 'jpg' if 'jpeg' in header or 'jpg' in header else 'png'
            filename = f"item_{session['user_id']}_{timestamp}.{ext}"
            
            # Save image
            upload_folder = os.path.join('static', 'images', 'food')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            image_file = filename
        except Exception as e:
            print(f"Error saving image: {e}")
            image_file = 'default.jpg'
    
    item = MenuItem(
        vendor_id=session['user_id'],
        name=data['name'],
        sub_name=data.get('sub_name'),
        category=data.get('category'),
        price=data['price'],
        is_available=data.get('is_available', True),
        image_file=image_file
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'image_file': image_file})

@app.route('/vendor/menu/<int:item_id>', methods=['PUT'])
@vendor_required
def edit_menu_item(item_id):
    import os
    import base64
    from datetime import datetime
    
    item = MenuItem.query.filter_by(id=item_id, vendor_id=session['user_id']).first()
    if not item:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.json
    item.name = data.get('name', item.name)
    item.sub_name = data.get('sub_name', item.sub_name)
    item.category = data.get('category', item.category)
    item.price = data.get('price', item.price)
    item.is_available = data.get('is_available', item.is_available)
    
    # Handle image update
    if data.get('image_file') and data['image_file'].startswith('data:image'):
        try:
            header, image_data = data['image_file'].split(',', 1)
            image_bytes = base64.b64decode(image_data)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ext = 'jpg' if 'jpeg' in header or 'jpg' in header else 'png'
            filename = f"item_{session['user_id']}_{timestamp}.{ext}"
            upload_folder = os.path.join('static', 'images', 'food')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            item.image_file = filename
        except Exception as e:
            print(f"Error saving image: {e}")
    
    db.session.commit()
    return jsonify({'success': True, 'image_file': item.image_file})

@app.route('/vendor/menu/<int:item_id>', methods=['DELETE'])
@vendor_required
def delete_menu_item(item_id):
    item = MenuItem.query.filter_by(id=item_id, vendor_id=session['user_id']).first()
    if not item:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/toggle_item/<int:item_id>', methods=['POST'])
@vendor_required
def toggle_item_availability(item_id):
    item = MenuItem.query.filter_by(id=item_id, vendor_id=session['user_id']).first()
    if not item:
        return jsonify({'error': 'Not found'}), 404
    
    item.is_available = not item.is_available
    db.session.commit()
    return jsonify({'success': True, 'is_available': item.is_available})

@app.route('/vendor/earnings')
@vendor_required
def vendor_earnings():
    from datetime import date, timedelta
    from sqlalchemy import func
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Total earnings
    total_earnings = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id==vendor_id, Order.status=='Completed'
    ).scalar() or 0
    
    # Today's earnings
    today = date.today()
    today_earnings = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id==vendor_id, func.date(Order.created_at)==today, Order.status=='Completed'
    ).scalar() or 0
    
    # Week earnings
    week_start = today - timedelta(days=today.weekday())
    week_earnings = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id==vendor_id, func.date(Order.created_at)>=week_start, Order.status=='Completed'
    ).scalar() or 0
    
    # Month earnings
    month_start = today.replace(day=1)
    month_earnings = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id==vendor_id, func.date(Order.created_at)>=month_start, Order.status=='Completed'
    ).scalar() or 0
    
    # Stats
    total_orders = Order.query.filter_by(vendor_id=vendor_id, status='Completed').count()
    completed_orders = total_orders
    all_orders = Order.query.filter_by(vendor_id=vendor_id).count()
    completion_rate = (completed_orders / all_orders * 100) if all_orders > 0 else 0
    avg_order_value = (total_earnings / total_orders) if total_orders > 0 else 0
    pending_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Chart data (last 7 days)
    chart_labels = []
    chart_values = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%d %b'))
        day_earnings = db.session.query(func.sum(Order.total)).filter(
            Order.vendor_id==vendor_id, func.date(Order.created_at)==day, Order.status=='Completed'
        ).scalar() or 0
        chart_values.append(float(day_earnings))
    
    # Recent orders
    earnings_history = Order.query.filter_by(vendor_id=vendor_id, status='Completed').order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('vendor/earnings.html',
                         total_earnings=total_earnings,
                         today_earnings=today_earnings,
                         week_earnings=week_earnings,
                         month_earnings=month_earnings,
                         month_growth=0,
                         week_growth=0,
                         total_orders=total_orders,
                         completed_orders=completed_orders,
                         completion_rate=completion_rate,
                         avg_order_value=avg_order_value,
                         pending_orders=pending_orders,
                         top_category='Food',
                         chart_labels=chart_labels,
                         chart_values=chart_values,
                         earnings_history=earnings_history,
                         vendor_profile=vendor,
                         unread_count=unread_count)

@app.route('/vendor/reviews')
@vendor_required
def vendor_reviews():
    from sqlalchemy import func
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Get reviews from orders
    reviews = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.review_rating!=None
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate stats
    total_count = len(reviews)
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
        Order.vendor_id==vendor_id, Order.review_rating!=None
    ).scalar() or 0
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Recent count (this month)
    from datetime import date
    month_start = date.today().replace(day=1)
    recent_count = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.review_rating!=None,
        func.date(Order.created_at)>=month_start
    ).count()
    
    return render_template('vendor/reviews.html',
                         reviews=reviews,
                         avg_rating=avg_rating,
                         total_count=total_count,
                         recent_count=recent_count,
                         response_rate=0,
                         responded_count=0,
                         vendor_profile=vendor,
                         unread_count=unread_count)

@app.route('/vendor/signup', methods=['GET', 'POST'])
def vendor_signup():
    if request.method == 'POST':
        business_name = request.form['business_name']
        email = request.form['email']
        business_category = request.form['business_category']
        business_address = request.form['business_address']
        phone = request.form['phone']
        password = request.form['password']

        # Check if email already exists
        existing_vendor = Vendor.query.filter_by(email=email).first()
        if existing_vendor:
            flash('Email already registered. Please use a different email or login.', 'error')
            return redirect(url_for('vendor_signup'))

        new_vendor = Vendor(business_name=business_name, email=email, business_category=business_category,
                           business_address=business_address, phone=phone)
        new_vendor.set_password(password)
        db.session.add(new_vendor)
        db.session.commit()

        session['user_id'] = new_vendor.id
        session['user_name'] = new_vendor.business_name
        session['user_email'] = new_vendor.email
        session['user_role'] = 'vendor'
        flash('Signup successful!', 'success')
        return redirect(url_for('vendor_dashboard'))

    return render_template('vendor/sign_up.html')

@app.route('/vendor/settings', methods=['GET', 'POST'])
@vendor_required
def vendor_settings():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    if request.method == 'POST':
        vendor.business_name = request.form.get('shop_name', vendor.business_name)
        vendor.email = request.form.get('email', vendor.email)
        vendor.business_category = request.form.get('business_category', vendor.business_category)
        vendor.phone = request.form.get('phone', vendor.phone)
        vendor.business_address = request.form.get('address', vendor.business_address)
        vendor.about = request.form.get('about', vendor.about)
        vendor.category_type = request.form.get('category_type')
        vendor.veg_nonveg = request.form.get('veg_nonveg')
        opening_time = request.form.get('opening_time')
        opening_period = request.form.get('opening_period')
        closing_time = request.form.get('closing_time')
        closing_period = request.form.get('closing_period')
        vendor.opening_time = f"{opening_time} {opening_period}" if opening_time and opening_period else None
        vendor.closing_time = f"{closing_time} {closing_period}" if closing_time and closing_period else None
        vendor.indoor_seating = request.form.get('indoor_seating') == '1'
        vendor.outdoor_seating = request.form.get('outdoor_seating') == '1'
        vendor.home_delivery = request.form.get('home_delivery') == '1'
        vendor.takeaway = request.form.get('takeaway') == '1'
        vendor.free_wifi = request.form.get('free_wifi') == '1'
        vendor.ac = request.form.get('ac') == '1'
        vendor.cooler = request.form.get('cooler') == '1'
        vendor.parking = request.form.get('parking')
        vendor.other_amenities = request.form.get('other_amenities')
        db.session.commit()
        
        # Update session
        session['user_name'] = vendor.business_name
        session['user_email'] = vendor.email
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('vendor_settings'))
    
    return render_template('vendor/settings.html', vendor_profile=vendor, unread_count=unread_count)

@app.route('/toggle_shop_status', methods=['POST'])
@vendor_required
def toggle_shop_status():
    data = request.json
    vendor = Vendor.query.get(session['user_id'])
    vendor.is_open = data.get('is_open', False)
    db.session.commit()
    return jsonify({'success': True, 'is_open': vendor.is_open})

@app.route('/vendor/update_shop_image', methods=['POST'])
@vendor_required
def update_shop_image():
    data = request.json
    vendor = Vendor.query.get(session['user_id'])
    vendor.shop_image = data.get('shop_image', '🏪')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/vendor/profile')
@vendor_required
def get_vendor_profile():
    vendor = Vendor.query.get(session['user_id'])
    return jsonify({
        'business_name': vendor.business_name,
        'email': vendor.email,
        'business_category': vendor.business_category,
        'business_address': vendor.business_address,
        'phone': vendor.phone
    })

@app.route('/vendor/update-profile', methods=['POST'])
@vendor_required
def update_vendor_profile():
    vendor = Vendor.query.get(session['user_id'])
    vendor.business_name = request.form.get('business_name', vendor.business_name)
    vendor.email = request.form.get('email', vendor.email)
    vendor.business_category = request.form.get('business_category', vendor.business_category)
    vendor.business_address = request.form.get('business_address', vendor.business_address)
    vendor.phone = request.form.get('phone', vendor.phone)
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('vendor_dashboard'))

@app.route('/map/<int:vendor_id>')
def map_view(vendor_id):
    return render_template("customer/map_view.html", vendor_id=vendor_id)

@app.route('/signup/success')
def signup_success():
    return render_template('success.html')
            
if __name__ == '__main__':
    app.run(debug=True)