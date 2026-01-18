#!/usr/bin/env python3
"""
Debug script to test SMS notifications
"""

from utils.twilio_notifications import TwilioNotifications
from models.models import db, Vendor, Order
from app import app

def debug_sms_issue():
    print("🔍 Debugging SMS notification issue...")
    print("=" * 50)

    with app.app_context():
        # Check if vendors exist
        vendors = Vendor.query.all()
        print(f"📊 Found {len(vendors)} vendors in database")

        if not vendors:
            print("❌ No vendors found in database")
            return

        for vendor in vendors:
            print(f"🏪 Vendor: {vendor.business_name} - Phone: {vendor.phone}")

        # Check recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(3).all()
        print(f"\n📦 Recent orders:")
        for order in recent_orders:
            print(f"   Order #{order.id}: {order.status} - Vendor: {order.vendor_name}")

        # Test Twilio connection
        print("\n🧪 Testing Twilio connection...")
        twilio = TwilioNotifications()

        # Test with a known working number
        test_phone = "+917777777777"  # Test number
        test_message = "🧪 LocalConnect SMS Test - Debug Mode"

        print(f"📤 Sending test SMS to {test_phone}...")
        success, result = twilio.send_confirmation_sms(test_phone, test_message)

        if success:
            print(f"✅ SMS sent successfully! SID: {result}")
        else:
            print(f"❌ SMS failed: {result}")

        # Test order notification format
        if recent_orders:
            latest_order = recent_orders[0]
            vendor = Vendor.query.filter_by(id=latest_order.vendor_id).first()

            if vendor:
                print("\n📋 Testing order notification format...")
                order_data = {
                    'id': latest_order.id,
                    'customer_name': latest_order.customer_name,
                    'items_summary': latest_order.items_summary,
                    'total': latest_order.total,
                    'delivery_type': latest_order.delivery_type,
                    'payment_type': latest_order.payment_type
                }

                print(f"📤 Would send to vendor phone: {vendor.phone}")
                print("📄 Message preview:")
                success, result = twilio.send_new_order_notification(vendor.phone, order_data)
                if success:
                    print(f"✅ Order notification sent! SID: {result}")
                else:
                    print(f"❌ Order notification failed: {result}")

if __name__ == "__main__":
    debug_sms_issue()
