#!/usr/bin/env python3
"""
Test order creation notification specifically
"""

from utils.twilio_notifications import TwilioNotifications
from models.models import db, Vendor, Customer, Order
from app import app

def test_order_creation_notification():
    print("🧪 Testing Order Creation Notification...")
    print("=" * 50)

    with app.app_context():
        # Get the latest order
        latest_order = Order.query.order_by(Order.created_at.desc()).first()

        if not latest_order:
            print("❌ No orders found in database")
            return

        print(f"📦 Testing with Order #{latest_order.id}")
        print(f"   Status: {latest_order.status}")
        print(f"   Customer: {latest_order.customer_name}")
        print(f"   Vendor: {latest_order.vendor_name}")

        # Get vendor
        vendor = Vendor.query.get(latest_order.vendor_id)
        if not vendor:
            print("❌ Vendor not found")
            return

        print(f"🏪 Vendor Phone: {vendor.phone}")

        # Get customer
        customer = Customer.query.get(latest_order.customer_id)
        if customer:
            print(f"👤 Customer Phone: {customer.phone}")

        # Prepare order data exactly like in create_order function
        order_data = {
            'id': latest_order.id,
            'customer_name': latest_order.customer_name,
            'items_summary': latest_order.items_summary,
            'total': latest_order.total,
            'delivery_type': latest_order.delivery_type,
            'payment_type': latest_order.payment_type
        }

        print("📄 Order Data:")
        print(f"   ID: {order_data['id']}")
        print(f"   Customer: {order_data['customer_name']}")
        print(f"   Items: {order_data['items_summary']}")
        print(f"   Total: ₹{order_data['total']}")
        print(f"   Type: {order_data['delivery_type']}")
        print(f"   Payment: {order_data['payment_type']}")

        # Test the notification
        twilio = TwilioNotifications()

        print(f"\n📤 Sending order notification to vendor {vendor.phone}...")
        success, result = twilio.send_new_order_notification(vendor.phone, order_data)

        if success:
            print(f"✅ Order notification sent successfully! SID: {result}")
        else:
            print(f"❌ Order notification failed: {result}")

        # Also test a simple confirmation SMS to the same number
        print(f"\n📤 Testing simple SMS to {vendor.phone}...")
        test_message = f"🧪 Test SMS from LocalConnect\nOrder #{latest_order.id} notification test\nTime: {twilio.ist.localize(twilio.ist.localize.now()).strftime('%I:%M %p')}"

        success2, result2 = twilio.send_confirmation_sms(vendor.phone, test_message)

        if success2:
            print(f"✅ Simple SMS sent successfully! SID: {result2}")
        else:
            print(f"❌ Simple SMS failed: {result2}")

if __name__ == "__main__":
    test_order_creation_notification()
