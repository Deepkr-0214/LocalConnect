from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    business_category = db.Column(db.String(50), nullable=False)
    business_address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_open = db.Column(db.Boolean, default=True)
    shop_image = db.Column(db.Text, default='🏪')
    about = db.Column(db.Text)
    category_type = db.Column(db.String(50))
    veg_nonveg = db.Column(db.String(20))
    indoor_seating = db.Column(db.Boolean, default=False)
    outdoor_seating = db.Column(db.Boolean, default=False)
    home_delivery = db.Column(db.Boolean, default=False)
    takeaway = db.Column(db.Boolean, default=False)
    free_wifi = db.Column(db.Boolean, default=False)
    ac = db.Column(db.Boolean, default=False)
    cooler = db.Column(db.Boolean, default=False)
    parking = db.Column(db.String(20))
    other_amenities = db.Column(db.Text)
    opening_time = db.Column(db.String(10))
    closing_time = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    menu_items = db.relationship('MenuItem', backref='vendor', lazy=True)
    orders = db.relationship('Order', backref='vendor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sub_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_file = db.Column(db.String(100), default='default.jpg')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    vendor_name = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    items = db.Column(db.Text, nullable=False)
    items_summary = db.Column(db.String(500))
    delivery_type = db.Column(db.String(20), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    order_type = db.Column(db.String(20))
    customer_suggestion = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Razorpay Details
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    
    review_rating = db.Column(db.Integer)
    review_comment = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    
    # Status timestamps
    preparing_at = db.Column(db.DateTime)
    out_for_delivery_at = db.Column(db.DateTime)
    ready_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    
    # Vendor Response Fields
    vendor_response = db.Column(db.Text)
    vendor_response_date = db.Column(db.DateTime)
    response_helpful = db.Column(db.Integer, default=0)
    
    def get_items(self):
        return json.loads(self.items)
    
    def set_items(self, items_list):
        self.items = json.dumps(items_list)
        self.items_summary = ', '.join([f"{item['name']} x{item['qty']}" for item in items_list])
