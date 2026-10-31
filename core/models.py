from django.db import models
from django.utils import timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')


class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.CharField(max_length=120, unique=True)
    phone = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=128)
    address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    home_latitude = models.FloatField(blank=True, null=True)
    home_longitude = models.FloatField(blank=True, null=True)
    current_latitude = models.FloatField(blank=True, null=True)
    current_longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customer'

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vendor(models.Model):
    id = models.AutoField(primary_key=True)
    business_name = models.CharField(max_length=100)
    email = models.CharField(max_length=120, unique=True)
    business_category = models.CharField(max_length=50)
    business_sub_category = models.CharField(max_length=50, blank=True, null=True)
    business_address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=128)
    is_open = models.BooleanField(default=True, blank=True, null=True)
    shop_image = models.TextField(default='🏪', blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    category_type = models.CharField(max_length=50, blank=True, null=True)
    veg_nonveg = models.CharField(max_length=20, blank=True, null=True)
    indoor_seating = models.BooleanField(default=False, blank=True, null=True)
    outdoor_seating = models.BooleanField(default=False, blank=True, null=True)
    home_delivery = models.BooleanField(default=False, blank=True, null=True)
    takeaway = models.BooleanField(default=False, blank=True, null=True)
    free_wifi = models.BooleanField(default=False, blank=True, null=True)
    ac = models.BooleanField(default=False, blank=True, null=True)
    cooler = models.BooleanField(default=False, blank=True, null=True)
    parking = models.CharField(max_length=20, blank=True, null=True)
    other_amenities = models.TextField(blank=True, null=True)
    opening_time = models.CharField(max_length=10, blank=True, null=True)
    closing_time = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vendor'

    def __str__(self):
        return self.business_name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MenuItem(models.Model):
    id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_column='vendor_id', related_name='menu_items')
    name = models.CharField(max_length=100)
    sub_name = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    price = models.FloatField()
    is_available = models.BooleanField(default=True, blank=True, null=True)
    image_file = models.CharField(max_length=100, default='default.jpg', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'menu_item'

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id', related_name='orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, db_column='vendor_id', related_name='orders')
    vendor_name = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    items = models.TextField()
    items_summary = models.CharField(max_length=500, blank=True, null=True)
    delivery_type = models.CharField(max_length=20)
    payment_type = models.CharField(max_length=20)
    total = models.FloatField()
    discount_amount = models.FloatField(default=0, blank=True, null=True)
    offer_title = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending', blank=True, null=True)
    order_type = models.CharField(max_length=20, blank=True, null=True)
    customer_suggestion = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    delivery_location_type = models.CharField(max_length=20, blank=True, null=True)
    vendor_latitude = models.FloatField(blank=True, null=True)
    vendor_longitude = models.FloatField(blank=True, null=True)
    customer_delivery_latitude = models.FloatField(blank=True, null=True)
    customer_delivery_longitude = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    # Razorpay Details
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Review Details
    review_rating = models.IntegerField(blank=True, null=True)
    review_comment = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)

    # Status timestamps
    preparing_at = models.DateTimeField(blank=True, null=True)
    out_for_delivery_at = models.DateTimeField(blank=True, null=True)
    ready_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    # Vendor Response Fields
    vendor_response = models.TextField(blank=True, null=True)
    vendor_response_date = models.DateTimeField(blank=True, null=True)
    response_helpful = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order'

    def __str__(self):
        return f"Order #{self.id} - {self.vendor_name} ({self.status})"

    def get_items(self):
        try:
            return json.loads(self.items)
        except Exception:
            return []

    def set_items(self, items_list):
        self.items = json.dumps(items_list)
        self.items_summary = ', '.join([f"{item.get('name', 'Item')} x{item.get('qty', 1)}" for item in items_list])


class Offer(models.Model):
    id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_column='vendor_id', related_name='offers')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=20)  # 'percentage' or 'flat'
    discount_value = models.FloatField()
    min_order = models.FloatField(default=0, blank=True, null=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    active = models.BooleanField(default=True, blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'offers'

    def __str__(self):
        return self.title

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_order': self.min_order or 0,
            'valid_from': self.valid_from.isoformat() if hasattr(self.valid_from, 'isoformat') else str(self.valid_from),
            'valid_to': self.valid_to.isoformat() if hasattr(self.valid_to, 'isoformat') else str(self.valid_to),
            'active': bool(self.active),
            'image': self.image or ''
        }


class VendorNotification(models.Model):
    id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_column='vendor_id', related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=50)  # 'new_order', 'payment', 'review', etc.
    is_read = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    order_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vendor_notification'

    def __str__(self):
        return f"{self.title} ({self.vendor})"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': bool(self.is_read),
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else str(self.created_at),
            'order_id': self.order_id,
            'time_ago': self.get_time_ago()
        }

    def get_time_ago(self):
        if not self.created_at:
            return "Just now"
        now = timezone.now()
        diff = now - self.created_at
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
