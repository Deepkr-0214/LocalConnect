from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, nullable=False, default=1)  # Added vendor_id to match main database
    name = db.Column(db.String(100), nullable=False)
    sub_name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_file = db.Column(db.String(100), default='default.jpg')
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    vendor_id = db.Column(db.Integer)
    vendor_name = db.Column(db.String(100))
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    items = db.Column(db.Text)
    items_summary = db.Column(db.String(500))
    delivery_type = db.Column(db.String(20))
    payment_type = db.Column(db.String(20))
    total = db.Column(db.Float)
    total_price = db.Column(db.Float)  # Keep for backward compatibility
    status = db.Column(db.String(20), default='Pending')
    order_type = db.Column(db.String(20))
    customer_suggestion = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    review_rating = db.Column(db.Integer)
    review_comment = db.Column(db.Text)
    review_date = db.Column(db.DateTime)
    
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False) # e.g., 4.5
    comment = db.Column(db.Text)
    response = db.Column(db.Text)  # Vendor response to the review
    response_date = db.Column(db.DateTime)  # When the response was posted
    is_helpful = db.Column(db.Boolean, default=False)  # Whether marked as helpful
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

# Ensure Vendor has these fields
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Localconnect Shop")
    email = db.Column(db.String(120), default="vendor@localconnect.com")
    phone = db.Column(db.String(20), default="+91 9876543210")
    address = db.Column(db.String(200), default="Indore, Vijay Nagar")
    is_open = db.Column(db.Boolean, default=True)