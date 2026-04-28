from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from models.models import db, Customer, Vendor, Order, MenuItem, Offer
import os
from datetime import datetime, timedelta, date
import json
from functools import wraps
import warnings
# Suppress razorpay deprecation warning
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
import razorpay
from dotenv import load_dotenv
import pytz
import logging
from utils.twilio_notifications import TwilioNotifications
from utils.enhanced_notifications import EnhancedNotifications
from utils.category_labels import get_category_labels
from geocoding_enhanced import GeocodeServiceEnhanced
from vendor_location_autofix import auto_fix_on_startup

# Load environment variables
load_dotenv()

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# Suppress verbose logging during startup
logging.basicConfig(
    level=logging.ERROR,
    format='%(message)s'
)
# Suppress all framework loggers
logging.getLogger('geocoding_enhanced').setLevel(logging.ERROR)
logging.getLogger('vendor_location_autofix').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.ERROR)

# Initialize enhanced geocoding service (silently)
import sys
old_stdout = sys.stdout
old_stderr = sys.stderr
try:
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    geocode_service = GeocodeServiceEnhanced()
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.permanent_session_lifetime = timedelta(hours=24)

# Configure session to be permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Initialize enhanced notification system
notifier = EnhancedNotifications()
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "instance", "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create database tables
with app.app_context():
    # Check if columns exist before adding them
    try:
        with db.engine.connect() as conn:
            # Check if columns exist first
            result = conn.execute(db.text("PRAGMA table_info('order')"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            columns_to_add = [
                ('preparing_at', 'DATETIME'),
                ('out_for_delivery_at', 'DATETIME'),
                ('ready_at', 'DATETIME'),
                ('completed_at', 'DATETIME'),
                ('rejected_at', 'DATETIME')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    conn.execute(db.text(f'ALTER TABLE "order" ADD COLUMN {column_name} {column_type}'))
            
            conn.commit()
    except Exception as e:
        pass  # Silently fail if columns already exist
    
    db.create_all()
    
    # Add offer and discount columns migration
    try:
        with db.engine.connect() as conn:
            # Check offers table and add image column
            result = conn.execute(db.text("PRAGMA table_info('offers')"))
            offers_columns = [row[1] for row in result.fetchall()]
            if 'image' not in offers_columns:
                conn.execute(db.text('ALTER TABLE offers ADD COLUMN image TEXT'))
            
            # Add discount columns to order table
            result = conn.execute(db.text("PRAGMA table_info('order')"))
            order_columns = [row[1] for row in result.fetchall()]
            if 'discount_amount' not in order_columns:
                conn.execute(db.text('ALTER TABLE "order" ADD COLUMN discount_amount FLOAT DEFAULT 0'))
            if 'offer_title' not in order_columns:
                conn.execute(db.text('ALTER TABLE "order" ADD COLUMN offer_title VARCHAR(200)'))
            
            # Add sub_category to vendor table
            result = conn.execute(db.text("PRAGMA table_info('vendor')"))
            vendor_columns = [row[1] for row in result.fetchall()]
            if 'business_sub_category' not in vendor_columns:
                conn.execute(db.text('ALTER TABLE vendor ADD COLUMN business_sub_category VARCHAR(50)'))
            
            conn.commit()
    except Exception as e:
        pass
    
    # Auto-fix all vendors with missing coordinates (silently in background)
    try:
        # Suppress all output during auto-fix
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        try:
            auto_fix_on_startup(app, db, Vendor, GeocodeServiceEnhanced)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    except Exception as e:
        pass  # Silently handle any errors

@app.before_request
def check_session_validity():
    """Check if the session is valid for protected routes"""
    # Skip session check for static files, login, signup, and public routes
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint in ['sign_in', 'customer_signup', 'vendor_signup', 'home', 'signup_success', 'forgot_password', 'reset_password', 'contact'] or
         request.endpoint.startswith('api.') or
         request.endpoint.startswith('get_vendor'))):
        return
    
    # Don't check session for API routes that don't require authentication
    if request.endpoint and request.endpoint.startswith('api.'):
        return

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debug logging
        print(f"DEBUG: Checking customer access for {request.endpoint}")
        print(f"DEBUG: Session data: {dict(session)}")
        
        # Check if user is logged in and has customer role
        if 'user_id' not in session or session.get('user_role') != 'customer':
            print(f"DEBUG: Session check failed - user_id: {session.get('user_id')}, role: {session.get('user_role')}")
            flash('Please login to access this page.', 'error')
            return redirect(url_for('sign_in'))
        
        # Verify that the customer still exists in database
        customer = Customer.query.get(session.get('user_id'))
        if not customer:
            print(f"DEBUG: Customer not found in database for ID: {session.get('user_id')}")
            # Clear session if customer no longer exists
            session.clear()
            flash('Account not found. Please login again.', 'error')
            return redirect(url_for('sign_in'))
        
        print(f"DEBUG: Customer access granted for {customer.full_name}")
        response = app.make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function

def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'vendor':
            flash('Access denied. Vendor login required.', 'error')
            return redirect(url_for('sign_in'))
        response = app.make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

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
                session.permanent = True
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
                session.permanent = True
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
    
    # Get customer coordinates if available
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    # Filter vendors by Food & Restaurant related categories
    food_categories = ['Food & Restaurant', 'Street Food', 'Food Shop', 'Restaurant', 'Dhaba', 'Street Food Carts', 'Food Shops', 'Restaurants & Dhabas']
    vendors = Vendor.query.filter(Vendor.business_category.in_(food_categories)).all()
    vendors_data = []
    
    for v in vendors:
        # Get min and max prices from vendor's menu
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 100
        max_price = int(price_query.max_price) if price_query.max_price else 300
        
        # Get rating stats from completed orders only
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if v.business_sub_category else v.business_category,
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '🏪',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/food&rest.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/garage')
@customer_required
def garage():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    # Filter vendors by Garage category
    vendors = Vendor.query.filter_by(business_category='Garage').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 250
        max_price = int(price_query.max_price) if price_query.max_price else 500
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else '2-Wheeler',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '🔧',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/garage.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/electronics')
@customer_required
def electronics():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    vendors = Vendor.query.filter_by(business_category='Electronics').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 10000
        max_price = int(price_query.max_price) if price_query.max_price else 50000
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else 'Mobiles',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '📱',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/electronics.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/fashion')
@customer_required
def fashion():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    vendors = Vendor.query.filter_by(business_category='Fashion').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 500
        max_price = int(price_query.max_price) if price_query.max_price else 1500
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else 'Ladies',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '👗',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/fashion.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/grocery')
@customer_required
def grocery():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    vendors = Vendor.query.filter_by(business_category='Grocery').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 80
        max_price = int(price_query.max_price) if price_query.max_price else 100
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else 'Vegetables',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '🛒',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/grocery.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/pharmacy')
@customer_required
def pharmacy():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    vendors = Vendor.query.filter_by(business_category='Pharmacy').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 80
        max_price = int(price_query.max_price) if price_query.max_price else 120
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else 'Ayurvedic Medicine',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '💊',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/pharmacy.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/books')
@customer_required
def books():
    from sqlalchemy import func
    user_id = session.get('user_id')
    
    customer = Customer.query.get(user_id)
    customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
    customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None
    
    vendors = Vendor.query.filter_by(business_category='Books').all()
    vendors_data = []
    
    for v in vendors:
        price_query = db.session.query(
            func.min(MenuItem.price).label('min_price'),
            func.max(MenuItem.price).label('max_price')
        ).filter_by(vendor_id=v.id).first()
        
        min_price = int(price_query.min_price) if price_query.min_price else 100
        max_price = int(price_query.max_price) if price_query.max_price else 500
        
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id==v.id, 
            Order.review_rating!=None,
            Order.status=='Completed'
        ).first()
        
        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0
        
        vendors_data.append({
            'id': v.id,
            'name': v.business_name,
            'category': v.business_category,
            'subcategory': v.business_sub_category if hasattr(v, 'business_sub_category') else 'Academic Books',
            'is_open': v.is_open if hasattr(v, 'is_open') else True,
            'shop_image': v.shop_image if hasattr(v, 'shop_image') else '📚',
            'address': v.business_address,
            'phone': v.phone,
            'min_price': min_price,
            'max_price': max_price,
            'latitude': v.latitude if hasattr(v, 'latitude') else None,
            'longitude': v.longitude if hasattr(v, 'longitude') else None,
            'rating': avg_rating,
            'review_count': review_count
        })
    
    return render_template('customer/books.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id, 
                         vendors=vendors_data,
                         customer_lat=customer_lat,
                         customer_lon=customer_lon)

@app.route('/customer/orders')
@customer_required
def customer_orders():
    user_id = session.get('user_id')
    orders_query = Order.query.filter_by(customer_id=user_id).order_by(Order.created_at.desc()).all()
    orders = [{
        'id': o.id,
        'vendor_id': o.vendor_id,
        'vendor_name': o.vendor_name,
        'items': o.items,
        'delivery_type': o.delivery_type,
        'payment_type': o.payment_type,
        'total': o.total,
        'status': o.status,
        'created_at': o.created_at.isoformat(),
        'preparing_at': o.preparing_at.isoformat() if o.preparing_at else None,
        'out_for_delivery_at': o.out_for_delivery_at.isoformat() if o.out_for_delivery_at else None,
        'ready_at': o.ready_at.isoformat() if o.ready_at else None,
        'completed_at': o.completed_at.isoformat() if o.completed_at else None,
        'review_rating': o.review_rating,
        'review_comment': o.review_comment,
        'rejectionReason': o.rejection_reason
    } for o in orders_query]
    return render_template('customer/orders.html', user_name=session.get('user_name'), user_id=user_id, orders=orders, orders_query=orders_query)

@app.route('/customer/profile')
@customer_required
def customer_profile():
    user_id = session.get('user_id')
    customer = Customer.query.get(user_id)
    return render_template('customer/profile.html', user_name=session.get('user_name'), customer=customer, user_id=user_id)

@app.route('/api/customer/profile', methods=['POST'])
@customer_required
def update_customer_profile():
    user_id = session.get('user_id')
    customer = Customer.query.get(user_id)
    if not customer:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Update only fields that are provided
        if 'full_name' in data and data['full_name']:
            customer.full_name = data['full_name'].strip()
            session['user_name'] = customer.full_name  # keep session in sync
        if 'email' in data and data['email']:
            # Check if email is already taken by another customer
            existing = Customer.query.filter(Customer.email == data['email'], Customer.id != user_id).first()
            if existing:
                return jsonify({'success': False, 'error': 'Email already in use by another account'}), 400
            customer.email = data['email'].strip()
            session['user_email'] = customer.email
        if 'phone' in data and data['phone']:
            customer.phone = data['phone'].strip()
        if 'address' in data:
            customer.address = data['address'].strip()
        if 'city' in data:
            customer.city = data['city'].strip()
        if 'state' in data:
            customer.state = data['state'].strip()
        if 'pincode' in data:
            customer.pincode = data['pincode'].strip()

        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/customer/vendor/<int:vendor_id>')
@customer_required
def vendor_details(vendor_id):
    user_id = session.get('user_id')
    vendor = Vendor.query.get_or_404(vendor_id)
    return render_template('customer/viewdet.html', vendor_id=vendor_id, vendor=vendor, user_name=session.get('user_name'), user_id=user_id)

@app.route('/customer/vendor/<int:vendor_id>/map')
@customer_required
def vendor_map(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if not vendor.latitude or not vendor.longitude:
        flash('Location not available for this vendor', 'warning')
        return redirect(url_for('vendor_details', vendor_id=vendor_id))
    return render_template('customer/map_view.html', vendor_id=vendor_id)

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

@app.route('/api/search/vendors', methods=['GET'])
def search_vendors():
    from sqlalchemy import or_, func
    search_term = request.args.get('q', '').strip().lower()
    
    if not search_term:
        return jsonify([])

    # A. Search vendors by name and category
    vendor_matches = Vendor.query.filter(
        or_(
            func.lower(Vendor.business_name).contains(search_term),
            func.lower(Vendor.business_category).contains(search_term)
        )
    ).all()
    
    # B. Search vendors by dish names in their menu
    dish_matches = db.session.query(Vendor).join(MenuItem).filter(
        func.lower(MenuItem.name).contains(search_term)
    ).distinct().all()
    
    # Combine results (unique vendors)
    all_matched_vendors = list(set(vendor_matches + dish_matches))
    
    vendors_data = []
    for v in all_matched_vendors:
        # Get matching dishes for THIS search term
        matching_dishes = MenuItem.query.filter(
            MenuItem.vendor_id == v.id,
            func.lower(MenuItem.name).contains(search_term)
        ).all()
        
        # Get rating stats
        rating_data = db.session.query(
            func.avg(Order.review_rating).label('avg_rating'),
            func.count(Order.review_rating).label('review_count')
        ).filter(
            Order.vendor_id == v.id,
            Order.review_rating != None,
            Order.status == 'Completed'
        ).first()

        avg_rating = round(rating_data.avg_rating, 1) if rating_data.avg_rating else 0
        review_count = rating_data.review_count if rating_data.review_count else 0

        # Get price range
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
            'subcategory': v.business_sub_category if v.business_sub_category else v.business_category,
            'cuisine': v.business_sub_category if v.business_sub_category else v.business_category,
            'rating': avg_rating,
            'reviews': review_count,
            'image': v.shop_image,
            'isOpen': v.is_open,
            'latitude': v.latitude,
            'longitude': v.longitude,
            'priceRange': f"₹{min_price}-{max_price}",
            'deliveryTime': '15-25 min',
            'matching_dishes': [dish.name for dish in matching_dishes]
        })
    
    return jsonify(vendors_data)

@app.route('/api/vendor/<int:vendor_id>/all-reviews')
def get_vendor_all_reviews(vendor_id):
    reviews = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.review_rating!=None,
        Order.status=='Completed'
    ).order_by(Order.review_date.desc()).all()
    
    return jsonify([{
        'customer_name': review.customer_name,
        'rating': review.review_rating,
        'comment': review.review_comment,
        'date': review.review_date.isoformat() if review.review_date else review.created_at.isoformat(),
        'vendor_response': review.vendor_response,
        'response_date': review.vendor_response_date.isoformat() if review.vendor_response_date else None,
        'helpful_count': review.response_helpful or 0,
        'vendor_name': review.vendor_name
    } for review in reviews])

@app.route('/api/vendor/<int:vendor_id>/reviews')
def get_vendor_reviews(vendor_id):
    from sqlalchemy import func
    rating_data = db.session.query(
        func.avg(Order.review_rating).label('avg_rating'),
        func.count(Order.review_rating).label('review_count')
    ).filter(
        Order.vendor_id==vendor_id, 
        Order.review_rating!=None,
        Order.status=='Completed'
    ).first()
    
    return jsonify({
        'avg_rating': round(rating_data.avg_rating, 1) if rating_data.avg_rating else 4.5,
        'review_count': rating_data.review_count if rating_data.review_count else 0
    })

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

        # Format phone number with +91 prefix if not already present
        if phone and not phone.startswith('+91'):
            if phone.startswith('91'):
                phone = f"+{phone}"
            else:
                phone = f"+91{phone.lstrip('0')}"

        new_customer = Customer(full_name=full_name, email=email, phone=phone)
        new_customer.set_password(password)
        db.session.add(new_customer)
        db.session.commit()

        session.permanent = True
        session['user_id'] = new_customer.id
        session['user_name'] = new_customer.full_name
        session['user_email'] = new_customer.email
        session['user_role'] = 'customer'
        
        # Send welcome notification
        try:
            notifier.notify_customer_order_placed(phone, {
                'id': 'WELCOME',
                'vendor_name': 'LocalConnect',
                'total': '0'
            })
            print(f"Welcome notification sent to customer {full_name}")
        except Exception as e:
            print(f"Failed to send welcome notification: {e}")
        
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

        # Validate phone numbers
        if not vendor.phone or not vendor.phone.startswith('+91'):
            print(f"Warning: Vendor {vendor.business_name} has invalid phone number: {vendor.phone}")
            return jsonify({'error': 'Vendor phone number is not configured properly'}), 500

        if not customer.phone or not customer.phone.startswith('+91'):
            print(f"Warning: Customer {customer.full_name} has invalid phone number: {customer.phone}")
            return jsonify({'error': 'Customer phone number is not configured properly'}), 500

        # Validate location type for delivery orders
        location_type = data.get('locationType')
        if data['deliveryType'] == 'delivery' and not location_type:
             # Default to home if not specified (backward compatibility)
             location_type = 'home'

        # Get active coordinates based on location choice
        customer_delivery_lat = None
        customer_delivery_lon = None
        
        if data['deliveryType'] == 'delivery':
            if location_type == 'current':
                customer_delivery_lat = customer.current_latitude
                customer_delivery_lon = customer.current_longitude
                # Fallback to home/profile if current not set
                if not customer_delivery_lat or not customer_delivery_lon:
                    customer_delivery_lat = customer.latitude
                    customer_delivery_lon = customer.longitude
            else: # home
                customer_delivery_lat = customer.home_latitude
                customer_delivery_lon = customer.home_longitude
                # Fallback to profile address if home not specifically set
                if not customer_delivery_lat or not customer_delivery_lon:
                    customer_delivery_lat = customer.latitude
                    customer_delivery_lon = customer.longitude

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
            discount_amount=data.get('discount', 0),
            offer_title=data.get('offerTitle', ''),
            customer_suggestion=data.get('customerSuggestion', ''),
            status='Pending' if data['paymentType'] != 'online' else 'Payment Pending',
            created_at=datetime.now(IST),
            # Save location snapshot
            delivery_location_type=location_type,
            vendor_latitude=vendor.latitude,
            vendor_longitude=vendor.longitude,
            customer_delivery_latitude=customer_delivery_lat,
            customer_delivery_longitude=customer_delivery_lon
        )
        order.set_items(data['items'])
        db.session.add(order)
        db.session.commit()

        # Send notifications for cash payments
        # Online payments will send notification after verification
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

            # Send enhanced notifications to both customer and vendor
            try:
                # Notify customer that order was placed
                customer_result = notifier.notify_customer_order_placed(customer.phone, order_data)
                print(f"Customer order placed notification: {customer_result}")
                
                # Notify vendor of new order
                vendor_result = notifier.notify_vendor_new_order(vendor.phone, order_data)
                print(f"Vendor new order notification: {vendor_result}")
                
            except Exception as e:
                print(f"Failed to send enhanced notifications: {e}")
        else:
            print(f"Online payment order created: ID={order.id}. Waiting for payment verification.")

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
                
                # Send enhanced notifications after successful payment
                vendor = Vendor.query.get(order.vendor_id)
                customer = Customer.query.get(order.customer_id)
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
                        # Send payment confirmation and order notifications
                        customer_result = notifier.notify_customer_order_placed(customer.phone, order_data)
                        print(f"Payment confirmation notifications sent: {customer_result}")
                        
                        # Also send new order notification to vendor
                        vendor_result = notifier.notify_vendor_new_order(vendor.phone, order_data)
                        print(f"Vendor new order notification after payment: {vendor_result}")
                        
                    except Exception as e:
                        print(f"Failed to send enhanced payment notifications: {e}")

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

@app.route('/api/orders/<int:order_id>/vendor-response', methods=['POST'])
@vendor_required
def add_vendor_response(order_id):
    order = Order.query.filter_by(id=order_id, vendor_id=session['user_id']).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    data = request.json
    order.vendor_response = data['response']
    order.vendor_response_date = datetime.now(IST)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/orders/<int:order_id>/helpful', methods=['POST'])
def mark_response_helpful(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    order.response_helpful = (order.response_helpful or 0) + 1
    db.session.commit()
    
    return jsonify({'success': True, 'helpful_count': order.response_helpful})

@app.route('/api/orders/<int:order_id>/received', methods=['POST'])
@customer_required
def mark_order_received(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if order.status != 'out_for_delivery':
        return jsonify({'error': 'Order is not out for delivery'}), 400
    
    # Mark order as completed
    order.status = 'Completed'
    order.completed_at = datetime.now(IST)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order marked as received',
        'earnings_added': order.total,
        'vendor_id': order.vendor_id,
        'vendor_name': order.vendor_name
    })

@app.route('/api/orders/<int:order_id>/review', methods=['POST'])
@customer_required
def add_review(order_id):
    data = request.json
    order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
    if order:
        order.review_rating = data['rating']
        order.review_comment = data['comment']
        order.review_date = datetime.now(IST)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Order not found'}), 404

@app.route('/api/profile', methods=['POST'])
@customer_required
def update_profile():
    data = request.json
    customer = Customer.query.get(session['user_id'])
    if customer:
        # Update basic profile fields
        if 'full_name' in data:
            customer.full_name = data['full_name']
            session['user_name'] = data['full_name']  # Update session
        if 'email' in data:
            customer.email = data['email']
            session['user_email'] = data['email']  # Update session
        if 'phone' in data:
            customer.phone = data['phone']
        
        # Update address fields
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        pincode = data.get('pincode')
        
        customer.address = address
        customer.city = city
        customer.state = state
        customer.pincode = pincode
        
        # Geocode the full address to get coordinates
        if address:
            from utils.geocoding import geocode_address
            full_address = f"{address}, {city}, {state}, {pincode}".strip(', ')
            latitude, longitude = geocode_address(full_address)
            if latitude and longitude:
                customer.latitude = latitude
                customer.longitude = longitude
        
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Customer not found'}), 404

@app.route('/api/customer/set-home-location', methods=['POST'])
@customer_required
def set_home_location():
    data = request.json
    customer = Customer.query.get(session['user_id'])
    if customer:
        customer.home_latitude = data.get('home_latitude')
        customer.home_longitude = data.get('home_longitude')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Customer not found'}), 404

@app.route('/api/customer/update-current-location', methods=['POST'])
@customer_required
def update_current_location():
    data = request.json
    customer = Customer.query.get(session['user_id'])
    if customer:
        customer.current_latitude = data.get('current_latitude')
        customer.current_longitude = data.get('current_longitude')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Customer not found'}), 404

# Utility function to convert amount to words
def amount_to_words(amount):
    """Convert a numeric amount to Indian number words"""
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
    
    # Split into rupees and paise
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    
    result = ''
    
    if rupees == 0:
        result = 'Zero Rupees'
    else:
        # Handle crores
        if rupees >= 10000000:
            crores = rupees // 10000000
            result += convert_below_thousand(crores) + ' Crore '
            rupees %= 10000000
        
        # Handle lakhs
        if rupees >= 100000:
            lakhs = rupees // 100000
            result += convert_below_thousand(lakhs) + ' Lakh '
            rupees %= 100000
        
        # Handle thousands
        if rupees >= 1000:
            thousands = rupees // 1000
            result += convert_below_thousand(thousands) + ' Thousand '
            rupees %= 1000
        
        # Handle remaining hundreds, tens, ones
        if rupees > 0:
            result += convert_below_thousand(rupees) + ' '
        
        result += 'Rupees'
    
    # Add paise if present
    if paise > 0:
        result += ' and ' + convert_below_hundred(paise) + ' Paise'
    
    return result.strip() + ' Only'

@app.route('/invoice/<int:order_id>')
@customer_required
def invoice(order_id):
    """Generate invoice for completed orders"""
    user_id = session.get('user_id')
    
    # Fetch order and validate it belongs to the customer
    order = Order.query.filter_by(id=order_id, customer_id=user_id).first()
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('customer_orders'))
    
    # Only allow invoices for completed orders
    if order.status != 'Completed':
        flash('Invoice is only available for completed orders', 'warning')
        return redirect(url_for('customer_orders'))
    
    # Fetch vendor and customer details
    vendor = Vendor.query.get(order.vendor_id)
    customer = Customer.query.get(user_id)
    
    if not vendor or not customer:
        flash('Unable to generate invoice', 'error')
        return redirect(url_for('customer_orders'))
    
    # Parse order items
    items = order.get_items()
    
    # Convert amount to words
    amount_words = amount_to_words(order.total)
    
    # Prepare invoice data
    invoice_data = {
        'order': order,
        'vendor': vendor,
        'customer': customer,
        'items': items,
        'amount_words': amount_words,
        'item_count': len(items),
        'invoice_date': datetime.now(IST)
    }
    
    return render_template('customer/invoice.html', **invoice_data)


@app.route('/api/vendor/earnings', methods=['GET'])
@vendor_required
def api_vendor_earnings():
    """API endpoint to get vendor earnings data in JSON format for debugging."""
    from datetime import date
    from sqlalchemy import func
    from utils.order_filters import OrderFilters
    
    vendor_id = session['user_id']
    
    # Calculate earnings using DB aggregation
    total_earnings = OrderFilters.calculate_total_earnings(Order, db, vendor_id)
    today_earnings = OrderFilters.calculate_today_earnings(Order, db, vendor_id)
    week_earnings = OrderFilters.calculate_week_earnings(Order, db, vendor_id)
    month_earnings = OrderFilters.calculate_month_earnings(Order, db, vendor_id)
    
    # Get order counts for verification
    completed_orders = OrderFilters.get_completed_orders_count(Order, vendor_id)
    all_orders = Order.query.filter_by(vendor_id=vendor_id).count()
    
    # Manual verification query
    manual_total = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id == vendor_id,
        Order.status == 'Completed'
    ).scalar() or 0.0
    
    response_data = {
        'vendor_id': vendor_id,
        'total_earnings': float(total_earnings),
        'today_earnings': float(today_earnings),
        'week_earnings': float(week_earnings),
        'month_earnings': float(month_earnings),
        'completed_orders': completed_orders,
        'all_orders': all_orders,
        'manual_verification': float(manual_total),
        'calculation_match': abs(float(total_earnings) - float(manual_total)) < 0.01,
        'timestamp': date.today().isoformat()
    }
    
    # Add no-cache headers
    response = jsonify(response_data)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if user exists
        customer = Customer.query.filter_by(email=email).first()
        vendor = Vendor.query.filter_by(email=email).first()
        
        if customer or vendor:
            # Generate reset token (simple timestamp for demo)
            import time
            reset_token = str(int(time.time()))
            
            # Print reset link to terminal instead of sending email
            reset_link = f"http://127.0.0.1:5000/reset-password/{reset_token}?email={email}"
            print(f"\n=== PASSWORD RESET LINK ===")
            print(f"Email: {email}")
            print(f"Reset Link: {reset_link}")
            print(f"==============================\n")
            
            flash('Password reset link has been printed to terminal!', 'success')
        else:
            flash('Email not found in our records.', 'error')
        
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = request.args.get('email')
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('reset_password', token=token, email=email))
        
        # Update password
        customer = Customer.query.filter_by(email=email).first()
        vendor = Vendor.query.filter_by(email=email).first()
        
        if customer:
            customer.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')
        elif vendor:
            vendor.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')
        else:
            flash('Invalid reset link!', 'error')
        
        return redirect(url_for('sign_in'))
    
    return render_template('reset_password.html', token=token, email=email)

@app.route('/customer/change-password', methods=['GET', 'POST'])
@customer_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Get current customer
        customer = Customer.query.get(session['user_id'])
        
        # Check if current password is correct
        if not customer.check_password(current_password):
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('change_password'))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('change_password'))
        
        # Update password
        customer.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('customer_profile'))
    
    return render_template('customer/change_password.html')
@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('Logged out successfully!', 'success')
    
    # Create response with redirect to landing page
    response = redirect(url_for('home'))
    
    # Add cache control headers to prevent caching
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    from datetime import date
    from sqlalchemy import func
    from utils.order_filters import OrderFilters
    
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    
    # Get vendor category information
    category = vendor.business_category if vendor else 'Food & Restaurant'
    subcategory = vendor.business_sub_category if vendor else None
    
    # Recent orders (all statuses for display)
    orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(5).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    today = date.today()
    
    # Today's orders count - ONLY completed orders
    todays_orders = Order.query.filter(
        Order.vendor_id==vendor_id, 
        func.date(Order.created_at)==today,
        Order.status=='Completed'
    ).count()
    
    # Today's earnings - ONLY completed orders using DB aggregation
    todays_earnings = OrderFilters.calculate_today_earnings(Order, db, vendor_id)
    
    # Debug logging
    print(f"DEBUG Dashboard - Vendor ID: {vendor_id}")
    print(f"DEBUG Dashboard - Category: {category}, Subcategory: {subcategory}")
    print(f"DEBUG Dashboard - Today's Earnings: {todays_earnings}")
    
    # Verify with manual calculation
    manual_check = db.session.query(func.sum(Order.total)).filter(
        Order.vendor_id == vendor_id,
        Order.status == 'Completed',
        func.date(Order.created_at) == today
    ).scalar()
    print(f"DEBUG Dashboard - Manual Check: {manual_check}")
    
    pending_orders = unread_count
    
    # Average rating from completed orders only
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
        Order.vendor_id==vendor_id, 
        Order.review_rating!=None,
        Order.status=='Completed'
    ).scalar() or 0
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).limit(5).all()
    
    # Get category-specific labels
    labels = get_category_labels(category)
    
    # Add no-cache headers
    response = app.make_response(render_template('vendor/vendor_dashboard.html', 
                                               orders=orders, 
                                               vendor_profile=vendor, 
                                               unread_count=unread_count,
                                               todays_orders=todays_orders, 
                                               todays_earnings=todays_earnings, 
                                               pending_orders=pending_orders,
                                               avg_rating=avg_rating, 
                                               menu_items=menu_items,
                                               category=category,
                                               subcategory=subcategory,
                                               labels=labels))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response
@app.route('/vendor/delivery-map')
@vendor_required
def vendor_delivery_map():
    """Display delivery map for vendor"""
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/delivery_map.html', vendor_profile=vendor, labels=labels, category=category)

@app.route('/vendor/orders')
@vendor_required
def vendor_orders():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/orders.html', orders=orders, vendor_profile=vendor, unread_count=unread_count, labels=labels, category=category)

@app.route('/vendor/orders/<int:order_id>/status', methods=['POST'])
@vendor_required
def update_order_status(order_id):
    order = Order.query.filter_by(id=order_id, vendor_id=session['user_id']).first()
    if not order:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.json
    new_status = data['status']
    
    # Update order status
    order.status = new_status
    if data.get('rejection_reason'):
        order.rejection_reason = data['rejection_reason']
    
    # Store timestamp for each status change
    current_time = datetime.now(IST)
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
    
    db.session.commit()
    
    # Send enhanced notifications to customer about status change
    customer = Customer.query.get(order.customer_id)
    vendor = Vendor.query.get(order.vendor_id)
    if customer:
        order_data = {
            'id': order.id,
            'vendor_name': order.vendor_name,
            'rejection_reason': order.rejection_reason
        }
        
        try:
            # Use enhanced notification system
            result = notifier.notify_customer_order_status(
                customer.phone, order_data, new_status
            )
            print(f"Enhanced status notification sent to customer {customer.phone}: {result}")
            
            # If order completed, also notify vendor
            if new_status == 'Completed' and vendor:
                vendor_result = notifier.notify_vendor_order_completed(
                    vendor.phone, order_data
                )
                print(f"Vendor completion notification sent: {vendor_result}")
                
        except Exception as e:
            print(f"Enhanced notification failed: {e}")
    
    # Return success with earnings info if order completed
    response = {'success': True}
    if new_status == 'Completed':
        response['earnings_added'] = order.total
    
    return jsonify(response)

@app.route('/vendor/menu')
@vendor_required
def vendor_menu():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/menu.html', menu_items=menu_items, items=menu_items, vendor_profile=vendor, unread_count=unread_count, labels=labels, category=category)

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

@app.route('/vendor/force-fix-earnings')
@vendor_required
def force_fix_earnings():
    vendor_id = session['user_id']
    # Get all orders for this vendor
    all_orders = Order.query.filter_by(vendor_id=vendor_id).all()
    fixed_count = 0
    
    for order in all_orders:
        # If order has rejection_reason, it should be Rejected
        if order.rejection_reason and order.status != 'Rejected':
            print(f"Fixing order #{order.id}: {order.status} -> Rejected (has rejection reason)")
            order.status = 'Rejected'
            fixed_count += 1
    
    db.session.commit()
    flash(f'Force fixed {fixed_count} orders. Please refresh earnings page.', 'success')
    return redirect(url_for('vendor_earnings'))

@app.route('/vendor/fix-earnings')
@vendor_required
def fix_earnings():
    vendor_id = session['user_id']
    # Update any orders that have rejection_reason but wrong status
    orders_to_fix = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.rejection_reason.isnot(None),
        Order.status != 'Rejected'
    ).all()
    
    for order in orders_to_fix:
        order.status = 'Rejected'
    
    db.session.commit()
    flash(f'Fixed {len(orders_to_fix)} orders with incorrect status', 'success')
    return redirect(url_for('vendor_earnings'))

@app.route('/vendor/earnings')
@vendor_required
def vendor_earnings():
    from datetime import date, timedelta
    from sqlalchemy import func
    from utils.order_filters import OrderFilters
    
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # All earnings calculations use ONLY completed orders with DB aggregation
    total_earnings = OrderFilters.calculate_total_earnings(Order, db, vendor_id)
    today_earnings = OrderFilters.calculate_today_earnings(Order, db, vendor_id)
    week_earnings = OrderFilters.calculate_week_earnings(Order, db, vendor_id)
    month_earnings = OrderFilters.calculate_month_earnings(Order, db, vendor_id)
    
    # Debug logging
    print(f"DEBUG Earnings - Vendor ID: {vendor_id}")
    print(f"DEBUG Earnings - Total: {total_earnings}")
    print(f"DEBUG Earnings - Today: {today_earnings}")
    print(f"DEBUG Earnings - Week: {week_earnings}")
    print(f"DEBUG Earnings - Month: {month_earnings}")
    
    # Stats - only from completed orders
    completed_orders = OrderFilters.get_completed_orders_count(Order, vendor_id)
    total_orders = completed_orders  # For consistency
    all_orders = Order.query.filter_by(vendor_id=vendor_id).count()
    completion_rate = (completed_orders / all_orders * 100) if all_orders > 0 else 0
    avg_order_value = OrderFilters.calculate_average_order_value(Order, db, vendor_id)
    pending_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Chart data (last 7 days) - only completed orders with DB aggregation
    chart_labels, chart_values = OrderFilters.get_earnings_chart_data(Order, db, vendor_id, 7)
    
    # Recent orders (show all recent orders for reference, but earnings only from completed)
    earnings_history = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    # Add no-cache headers
    response = app.make_response(render_template('vendor/earnings.html',
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
                                               unread_count=unread_count,
                                               labels=labels,
                                               category=category))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/vendor/reviews')
@vendor_required
def vendor_reviews():
    from sqlalchemy import func
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Get reviews from completed orders only
    reviews = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.review_rating!=None,
        Order.status=='Completed'
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate stats
    total_count = len(reviews)
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
        Order.vendor_id==vendor_id, 
        Order.review_rating!=None,
        Order.status=='Completed'
    ).scalar() or 0
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Recent count (this month)
    from datetime import date
    month_start = date.today().replace(day=1)
    recent_count = Order.query.filter(
        Order.vendor_id==vendor_id,
        Order.review_rating!=None,
        func.date(Order.created_at)>=month_start,
        Order.status=='Completed'
    ).count()
    
    # Response stats
    responded_count = len([r for r in reviews if r.vendor_response])
    response_rate = round((responded_count / total_count * 100) if total_count > 0 else 0)
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/reviews.html',
                         reviews=reviews,
                         avg_rating=avg_rating,
                         total_count=total_count,
                         recent_count=recent_count,
                         response_rate=response_rate,
                         responded_count=responded_count,
                         vendor_profile=vendor,
                         unread_count=unread_count,
                         labels=labels,
                         category=category)

@app.route('/vendor/signup', methods=['GET', 'POST'])
def vendor_signup():
    if request.method == 'POST':
        business_name = request.form['business_name']
        email = request.form['email']
        business_category = request.form['business_category']
        business_address = request.form['business_address']
        phone = request.form['phone']
        password = request.form['password']

        # Log vendor registration attempt
        app_logger.info(f"=== NEW VENDOR REGISTRATION ===")
        app_logger.info(f"Business: {business_name}")
        app_logger.info(f"Email: {email}")
        app_logger.info(f"Address: {business_address}")

        # Check if email already exists
        existing_vendor = Vendor.query.filter_by(email=email).first()
        if existing_vendor:
            flash('Email already registered. Please use a different email or login.', 'error')
            return redirect(url_for('vendor_signup'))

        # Format phone number with +91 prefix if not already present
        if phone and not phone.startswith('+91'):
            if phone.startswith('91'):
                phone = f"+{phone}"
            else:
                phone = f"+91{phone.lstrip('0')}"

        new_vendor = Vendor(business_name=business_name, email=email, business_category=business_category,
                           business_sub_category=request.form.get('business_sub_category'),
                           category_type=request.form.get('business_sub_category'),
                           business_address=business_address, phone=phone)
        new_vendor.set_password(password)
        
        # Geocode the business address using enhanced service
        app_logger.info(f"Starting geocoding for address: {business_address}")
        latitude, longitude = geocode_service.geocode(business_address)
        
        if latitude and longitude:
            new_vendor.latitude = latitude
            new_vendor.longitude = longitude
            geocoding_status = '✅ Location detected automatically!'
            app_logger.info(f"✅ GEOCODING SUCCESS: ({latitude:.4f}, {longitude:.4f})")
            app_logger.info(f"Vendor will appear on map at correct location")
        else:
            geocoding_status = '⚠️ Location could not be detected. Please try with a more complete address (include city and state).'
            app_logger.error(f"❌ GEOCODING FAILED for vendor: {business_name}")
            app_logger.error(f"   Address: {business_address}")
            app_logger.error(f"   Vendor may not appear on map until coordinates are updated")
        
        db.session.add(new_vendor)
        db.session.commit()

        app_logger.info(f"Vendor created with ID: {new_vendor.id}")
        app_logger.info(f"Latitude: {new_vendor.latitude}, Longitude: {new_vendor.longitude}")

        session.permanent = True
        session['user_id'] = new_vendor.id
        session['user_name'] = new_vendor.business_name
        session['user_email'] = new_vendor.email
        session['user_role'] = 'vendor'
        
        # Send welcome notification
        try:
            enhanced_notifications.notify_vendor_welcome(phone, business_name)
            print(f"Welcome notification sent to vendor {business_name}")
        except Exception as e:
            print(f"Failed to send welcome notification: {e}")
        
        flash(f'Signup successful! {geocoding_status}', 'success')
        return redirect(url_for('vendor_dashboard'))

    return render_template('vendor/sign_up.html')

@app.route('/vendor/change-password', methods=['GET', 'POST'])
@vendor_required
def vendor_change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Get current vendor
        vendor = Vendor.query.get(session['user_id'])
        
        # Check if current password is correct
        if not vendor.check_password(current_password):
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('vendor_change_password'))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('vendor_change_password'))
        
        # Update password
        vendor.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('vendor_settings'))
    
    vendor = Vendor.query.get(session['user_id'])
    unread_count = Order.query.filter_by(vendor_id=session['user_id'], status='Pending').count()
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/change_password.html', vendor_profile=vendor, unread_count=unread_count, labels=labels, category=category)

@app.route('/vendor/settings', methods=['GET', 'POST'])
@vendor_required
def vendor_settings():
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Get vendor offers for the offers section
    try:
        offers = Offer.query.filter_by(vendor_id=vendor_id).all()
    except:
        offers = []
    
    if request.method == 'POST':
        # Check if address is being updated
        new_address = request.form.get('address')
        address_changed = new_address and new_address != vendor.business_address
        
        vendor.business_name = request.form.get('shop_name', vendor.business_name)
        vendor.email = request.form.get('email', vendor.email)
        vendor.business_category = request.form.get('business_category', vendor.business_category)
        vendor.business_sub_category = request.form.get('business_sub_category', vendor.business_sub_category)
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
        
        # If address changed, geocode the new address using enhanced service
        if address_changed:
            app_logger.info(f"=== VENDOR ADDRESS UPDATE ===")
            app_logger.info(f"Vendor ID: {vendor_id}")
            app_logger.info(f"Old address: {vendor.business_address}")
            app_logger.info(f"New address: {new_address}")
            app_logger.info(f"Starting geocoding for new address...")
            
            latitude, longitude = geocode_service.geocode(new_address)
            
            if latitude and longitude:
                vendor.latitude = latitude
                vendor.longitude = longitude
                location_message = '✅ Location updated automatically!'
                app_logger.info(f"✅ GEOCODING SUCCESS: ({latitude:.4f}, {longitude:.4f})")
                app_logger.info(f"Vendor location updated on map")
            else:
                location_message = '⚠️ Address updated, but location could not be detected. Try a more complete address.'
                app_logger.error(f"❌ GEOCODING FAILED for vendor: {vendor.business_name}")
                app_logger.error(f"   New address: {new_address}")
        else:
            location_message = None
        
        # Handle manual GPS coordinates from shop location field
        if 'latitude' in request.form and 'longitude' in request.form:
            try:
                manual_lat = float(request.form.get('latitude'))
                manual_lng = float(request.form.get('longitude'))
                if -90 <= manual_lat <= 90 and -180 <= manual_lng <= 180:
                    vendor.latitude = manual_lat
                    vendor.longitude = manual_lng
                    location_message = 'GPS location updated successfully!'
                    app_logger.info(f"Manual GPS coordinates set: ({manual_lat:.6f}, {manual_lng:.6f})")
            except (ValueError, TypeError):
                pass
        
        db.session.commit()
        
        # Update session
        session['user_name'] = vendor.business_name
        session['user_email'] = vendor.email
        
        if location_message:
            flash(f'Settings updated successfully! {location_message}', 'success')
        else:
            flash('Settings updated successfully!', 'success')
        return redirect(url_for('vendor_settings'))
    
    # Get category-specific labels
    category = vendor.business_category if vendor else 'Food & Restaurant'
    labels = get_category_labels(category)
    
    return render_template('vendor/settings.html', vendor_profile=vendor, unread_count=unread_count, offers=offers, labels=labels, category=category)

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

@app.route('/api/twilio/webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming WhatsApp messages from vendors to accept/reject orders"""
    try:
        from_number = request.form.get('From')
        message_body = request.form.get('Body')
        
        print(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Process the WhatsApp reply
        action, order_id, reason = twilio_notifications.process_vendor_whatsapp_reply(from_number, message_body)
        
        if action and order_id:
            # Remove whatsapp: prefix from phone number for vendor lookup
            vendor_phone = from_number.replace('whatsapp:', '') if from_number.startswith('whatsapp:') else from_number
            
            # Find the vendor by phone number
            vendor = Vendor.query.filter_by(phone=vendor_phone).first()
            if not vendor:
                # Send error message
                twilio_notifications.send_confirmation_whatsapp(
                    from_number, 
                    "❌ Phone number not registered as vendor. Please contact support."
                )
                return '', 200
            
            # Find the order
            order = Order.query.filter_by(id=order_id, vendor_id=vendor.id).first()
            if not order:
                twilio_notifications.send_confirmation_whatsapp(
                    from_number,
                    f"❌ Order #{order_id} not found or not assigned to your shop."
                )
                return '', 200
            
            if order.status != 'Pending':
                twilio_notifications.send_confirmation_whatsapp(
                    from_number,
                    f"❌ Order #{order_id} has already been processed (Status: {order.status})."
                )
                return '', 200
            
            # Update order status
            current_time = datetime.now(IST)
            
            if action == 'accept':
                order.status = 'preparing'
                order.preparing_at = current_time
                
                # Send confirmation to vendor
                enhanced_notifications.send_dual_notification(
                    from_number,
                    f"✅ Order #{order_id} ACCEPTED and marked as preparing. Customer has been notified."
                )
                
                # Send notification to customer using enhanced system
                customer = Customer.query.get(order.customer_id)
                if customer:
                    order_data = {
                        'id': order.id,
                        'vendor_name': order.vendor_name
                    }
                    enhanced_notifications.notify_customer_order_status(
                        customer.phone, order_data, 'accepted'
                    )
            
            elif action == 'reject':
                order.status = 'Rejected'
                order.rejection_reason = reason
                order.rejected_at = current_time
                
                # Send confirmation to vendor
                enhanced_notifications.send_dual_notification(
                    from_number,
                    f"❌ Order #{order_id} REJECTED. Customer has been notified."
                )
                
                # Send notification to customer using enhanced system
                customer = Customer.query.get(order.customer_id)
                if customer:
                    order_data = {
                        'id': order.id,
                        'vendor_name': order.vendor_name,
                        'rejection_reason': reason
                    }
                    enhanced_notifications.notify_customer_order_status(
                        customer.phone, order_data, 'Rejected'
                    )
            
            db.session.commit()
            print(f"Order #{order_id} {action}ed via WhatsApp by vendor {vendor.business_name}")
        
        else:
            # Invalid WhatsApp message format
            enhanced_notifications.send_dual_notification(
                from_number,
                "❓ Invalid format. Use:\n• ACCEPT [order_id]\n• REJECT [order_id] [reason]"
            )
        
        return '', 200
        
    except Exception as e:
        print(f"Error processing Twilio WhatsApp webhook: {e}")
        return '', 500

@app.route('/api/twilio/test-notification', methods=['POST'])
@vendor_required
def test_twilio_notification():
    """Test endpoint for vendors to test SMS notifications"""
    try:
        vendor = Vendor.query.get(session['user_id'])
        
        # Send enhanced test notification
        test_message = f"📱 TEST NOTIFICATION from LocalConnect!\n\nHi {vendor.business_name},\nYour SMS and WhatsApp notifications are working correctly.\n\nTime: {datetime.now(IST).strftime('%I:%M %p')}"
        
        result = enhanced_notifications.send_dual_notification(vendor.phone, test_message, 'test')
        
        if result['sms'] or result['whatsapp']:
            return jsonify({
                'success': True, 
                'message': 'Test notifications sent successfully!',
                'details': result
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Both SMS and WhatsApp failed',
                'details': result
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/customer/test-notification', methods=['POST'])
@customer_required
def test_customer_notification():
    """Test endpoint for customers to test SMS and WhatsApp notifications"""
    try:
        customer = Customer.query.get(session['user_id'])
        
        test_message = f"📱 TEST NOTIFICATION from LocalConnect!\n\nHi {customer.full_name},\nYour SMS and WhatsApp notifications are working correctly.\n\nYou'll receive updates about your orders on both channels.\n\nTime: {datetime.now(IST).strftime('%I:%M %p')}"
        
        result = enhanced_notifications.send_dual_notification(customer.phone, test_message, 'test')
        
        if result['sms'] or result['whatsapp']:
            return jsonify({
                'success': True, 
                'message': 'Test notifications sent successfully!',
                'details': result
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Both SMS and WhatsApp failed',
                'details': result
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/customer/notification-settings')
@customer_required
def customer_notification_settings():
    """Customer notification settings page"""
    user_id = session.get('user_id')
    return render_template('customer/notification_settings.html', 
                         user_name=session.get('user_name'), 
                         user_id=user_id)

@app.route('/vendor/notification-settings')
@vendor_required
def vendor_notification_settings():
    """Vendor notification settings page"""
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    return render_template('vendor/notification_settings.html', 
                         vendor_profile=vendor, 
                         unread_count=unread_count)

@app.route('/api/customer/notification-settings', methods=['POST'])
@customer_required
def save_customer_notification_settings():
    """Save customer notification preferences"""
    try:
        # For now, just return success as we don't have a settings table yet
        # In a full implementation, you would save these to a customer_notification_settings table
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/vendor/notification-dashboard')
@vendor_required
def vendor_notification_dashboard():
    """Vendor notification dashboard page"""
    vendor_id = session['user_id']
    vendor = Vendor.query.get(vendor_id)
    unread_count = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    return render_template('vendor/notification_dashboard.html', 
                         vendor_profile=vendor, 
                         unread_count=unread_count)

@app.route('/api/vendor/notification-dashboard')
@vendor_required
def api_vendor_notification_dashboard():
    """API endpoint for notification dashboard data"""
    try:
        # In a full implementation, you would track notification history in a database
        # For now, return mock data
        return jsonify({
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
                    'message': 'New order #123 received from customer...'
                },
                {
                    'timestamp': (datetime.now()).isoformat(),
                    'type': 'payment_received',
                    'recipient': '+91XXXXXXXXXX',
                    'sms_success': True,
                    'whatsapp_success': False,
                    'message': 'Payment confirmed for order #122...'
                }
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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

@app.route('/api/vendor/sms-status-update', methods=['POST'])
@vendor_required
def sms_status_update():
    """Allow vendors to update order status via web interface and send SMS to customer"""
    try:
        data = request.json
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        order = Order.query.filter_by(id=order_id, vendor_id=session['user_id']).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Update order status with timestamp
        current_time = datetime.now(IST)
        order.status = new_status
        
        if new_status == 'ready':
            order.ready_at = current_time
        elif new_status == 'out_for_delivery':
            order.out_for_delivery_at = current_time
        elif new_status == 'Completed':
            order.completed_at = current_time
        
        db.session.commit()
        
        # Send SMS notification to customer
        customer = Customer.query.get(order.customer_id)
        if customer:
            order_data = {
                'id': order.id,
                'vendor_name': order.vendor_name
            }
            
            success, result = twilio_notifications.send_order_status_notification(
                customer.phone, order_data, new_status
            )
            
            if success:
                return jsonify({
                    'success': True, 
                    'message': f'Order status updated and SMS sent to customer',
                    'sms_id': result
                })
            else:
                return jsonify({
                    'success': True, 
                    'message': 'Order status updated but SMS failed',
                    'sms_error': result
                })
        
        return jsonify({'success': True, 'message': 'Order status updated'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer/sms-order-received', methods=['POST'])
@customer_required
def sms_order_received():
    """Allow customers to mark order as received via SMS confirmation"""
    try:
        data = request.json
        order_id = data.get('order_id')
        
        order = Order.query.filter_by(id=order_id, customer_id=session['user_id']).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if order.status != 'out_for_delivery':
            return jsonify({'error': 'Order is not out for delivery'}), 400
        
        # Mark order as completed
        order.status = 'Completed'
        order.completed_at = datetime.now(IST)
        db.session.commit()
        
        # Send confirmation SMS to customer
        customer = Customer.query.get(session['user_id'])
        vendor = Vendor.query.get(order.vendor_id)
        
        confirmation_message = f"✅ Order #{order.id} marked as received!\n\nThank you for choosing {order.vendor_name}!\nTotal: ₹{order.total}\n\nPlease rate your experience on our app."
        
        success, result = twilio_notifications.send_confirmation_sms(customer.phone, confirmation_message)
        
        # Send notification to vendor about completion
        if vendor:
            vendor_message = f"🎉 Order #{order.id} completed!\n\nCustomer: {order.customer_name}\nTotal: ₹{order.total}\nEarnings added to your account."
            twilio_notifications.send_confirmation_sms(vendor.phone, vendor_message)
        
        return jsonify({
            'success': True,
            'message': 'Order marked as received',
            'earnings_added': order.total,
            'vendor_id': order.vendor_id,
            'vendor_name': order.vendor_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/vendor/current')
@vendor_required
def get_current_vendor():
    """API endpoint to get current logged-in vendor information"""
    vendor = Vendor.query.get(session['user_id'])
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    return jsonify({
        'id': vendor.id,
        'business_name': vendor.business_name,
        'latitude': vendor.latitude,
        'longitude': vendor.longitude,
        'business_address': vendor.business_address,
        'phone': vendor.phone
    })

@app.route('/api/vendor/deliveries/active')
@vendor_required
def get_active_deliveries():
    """API endpoint to get active home delivery orders for the vendor"""
    vendor_id = session['user_id']
    
    # Get active home delivery orders
    deliveries = Order.query.filter(
        Order.vendor_id == vendor_id,
        Order.delivery_type == 'delivery',
        Order.status.in_(['out_for_delivery', 'preparing', 'ready'])
    ).order_by(Order.created_at.desc()).all()
    
    delivery_list = []
    for order in deliveries:
        # Use order-specific coordinates as requested
        # Fallback to profile coordinates if order coordinates are missing (legacy data)
        customer_lat = order.customer_delivery_latitude
        customer_lon = order.customer_delivery_longitude
        
        vendor_lat = order.vendor_latitude
        vendor_lon = order.vendor_longitude
        
        if not customer_lat or not customer_lon:
            customer = Customer.query.get(order.customer_id)
            customer_lat = customer.latitude if customer and hasattr(customer, 'latitude') else None
            customer_lon = customer.longitude if customer and hasattr(customer, 'longitude') else None

        # If vendor coords missing in order, get from vendor profile
        if not vendor_lat or not vendor_lon:
            vendor = Vendor.query.get(vendor_id)
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
            'created_at': order.created_at.isoformat()
        })
    
    return jsonify(delivery_list)

@app.route('/api/vendor/<int:vendor_id>/location')
def get_vendor_location(vendor_id):
    """API endpoint to get vendor location data for maps"""
    vendor = Vendor.query.get(vendor_id)
    if not vendor:
        return jsonify({'error': 'Vendor not found'}), 404
    
    return jsonify({
        'id': vendor.id,
        'name': vendor.business_name,
        'category': vendor.business_category,
        'address': vendor.business_address,
        'phone': vendor.phone,
        'latitude': vendor.latitude,
        'longitude': vendor.longitude,
        'is_open': vendor.is_open if hasattr(vendor, 'is_open') else True,
        'about': vendor.about,
        'opening_time': vendor.opening_time if hasattr(vendor, 'opening_time') else None,
        'closing_time': vendor.closing_time if hasattr(vendor, 'closing_time') else None
    })

@app.route('/map/<int:vendor_id>')
def map_view(vendor_id):
    return render_template("customer/map_view.html", vendor_id=vendor_id)

@app.route('/signup/success')
def signup_success():
    return render_template('success.html')

# Admin routes for vendor management
@app.route('/admin/delete-vendors')
def admin_delete_vendors_page():
    """Admin page to delete all vendors"""
    return render_template('admin/delete_vendors.html')

@app.route('/admin/delete-all-vendors', methods=['POST'])
def delete_all_vendors():
    """Delete all vendors and their associated data"""
    try:
        # Delete all menu items first (foreign key constraint)
        MenuItem.query.delete()
        
        # Update orders to remove vendor references
        orders = Order.query.all()
        for order in orders:
            if order.vendor_id:
                order.vendor_name = f"Deleted Vendor (ID: {order.vendor_id})"
                order.vendor_id = None
        
        # Delete all vendors
        vendor_count = Vendor.query.count()
        Vendor.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted {vendor_count} vendors and all associated menu items',
            'deleted_count': vendor_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Customer account deletion
@app.route('/customer/delete-account', methods=['POST'])
@customer_required
def delete_customer_account():
    """Permanently delete customer account and all associated data"""
    try:
        customer_id = session['user_id']
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        # Delete all customer orders
        Order.query.filter_by(customer_id=customer_id).delete()
        
        # Delete customer account
        db.session.delete(customer)
        db.session.commit()
        
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True, 
            'message': 'Account permanently deleted',
            'redirect': url_for('home')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Vendor account deletion
@app.route('/vendor/delete-account', methods=['POST'])
@vendor_required
def delete_vendor_account():
    """Permanently delete vendor account and all associated data"""
    try:
        vendor_id = session['user_id']
        vendor = Vendor.query.get(vendor_id)
        
        if not vendor:
            return jsonify({'success': False, 'error': 'Vendor not found'}), 404
        
        # Delete all menu items first
        MenuItem.query.filter_by(vendor_id=vendor_id).delete()
        
        # Update orders to remove vendor reference but keep order history
        orders = Order.query.filter_by(vendor_id=vendor_id).all()
        for order in orders:
            order.vendor_name = f"Deleted Vendor: {vendor.business_name}"
            order.vendor_id = None
        
        # Delete vendor account completely
        vendor_email = vendor.email
        db.session.delete(vendor)
        db.session.commit()
        
        # Clear session completely
        session.clear()
        
        print(f"Vendor account deleted: {vendor_email}")
        
        return jsonify({
            'success': True, 
            'message': 'Account permanently deleted',
            'redirect': url_for('home')
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting vendor account: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
            
@app.route('/vendor/offers/list')
@vendor_required
def get_vendor_offers_list():
    try:
        offers = Offer.query.filter_by(vendor_id=session['user_id']).all()
        return jsonify([offer.to_dict() for offer in offers])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/vendor/offers/get/<int:offer_id>')
@vendor_required
def get_vendor_offer(offer_id):
    try:
        offer = Offer.query.filter_by(id=offer_id, vendor_id=session['user_id']).first()
        if not offer:
            return jsonify({'success': False, 'error': 'Offer not found'}), 404
        return jsonify({'success': True, 'offer': offer.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Vendor Offers API Routes
@app.route('/vendor/offers/add', methods=['POST'])
@vendor_required
def add_vendor_offer():
    try:
        data = request.json
        offer = Offer(
            vendor_id=session['user_id'],
            title=data['title'],
            description=data['description'],
            discount_type=data['discount_type'],
            discount_value=data['discount_value'],
            min_order=data.get('min_order', 0),
            valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d').date(),
            valid_to=datetime.strptime(data['valid_to'], '%Y-%m-%d').date(),
            active=data.get('active', True),
            image=data.get('image')
        )
        db.session.add(offer)
        db.session.commit()
        return jsonify({'success': True, 'offer': offer.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/vendor/offers/edit/<int:offer_id>', methods=['POST'])
@vendor_required
def edit_vendor_offer(offer_id):
    try:
        offer = Offer.query.filter_by(id=offer_id, vendor_id=session['user_id']).first()
        if not offer:
            return jsonify({'success': False, 'error': 'Offer not found'}), 404
        
        data = request.json
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
        
        db.session.commit()
        return jsonify({'success': True, 'offer': offer.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/vendor/offers/delete/<int:offer_id>', methods=['POST'])
@vendor_required
def delete_vendor_offer(offer_id):
    offer = Offer.query.filter_by(id=offer_id, vendor_id=session['user_id']).first()
    if not offer:
        return jsonify({'error': 'Offer not found'}), 404
    
    db.session.delete(offer)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/vendor/<int:vendor_id>/offers')
def get_vendor_offers(vendor_id):
    today = date.today()
    offers = Offer.query.filter(
        Offer.vendor_id == vendor_id,
        Offer.active == True,
        Offer.valid_from <= today,
        Offer.valid_to >= today
    ).all()
    return jsonify([offer.to_dict() for offer in offers])

@app.route('/chat', methods=['POST'])
@customer_required
def chat():
    from utils.chatbot_logic import chat_logic
    return chat_logic()

if __name__ == '__main__':
    # Local development only - NOT USED by Gunicorn on Railway/Render
    # Gunicorn imports this module and extracts 'app' directly without executing this block
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    port = int(os.getenv('PORT', 5000))
    print(f"\n[OK] Local development server starting at http://localhost:{port}\n")
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True, use_debugger=False)
