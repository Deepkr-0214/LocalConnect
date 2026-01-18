#!/usr/bin/env python3
"""
Test WhatsApp notification when customer books order
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.twilio_notifications import TwilioNotifications
from models.models import db, Order, Vendor, Customer
from app import app

def test_whatsapp_notification():
    """Test WhatsApp notification to vendor"""
    
    with app.app_context():
        print("🧪 Testing WhatsApp Notification...")
        print("=" * 50)
        
        # Get first vendor
        vendor = Vendor.query.first()
        if not vendor:
            print("❌ No vendor found. Please add test data first.")
            return False
        
        print(f"📱 Testing with Vendor: {vendor.business_name}")
        print(f"📞 Vendor Phone: {vendor.phone}")
        
        # Check if phone number is valid
        if not vendor.phone or not vendor.phone.startswith('+91'):
            print("❌ Vendor phone number is invalid. Must start with +91")
            return False
        
        # Create test order data
        test_order_data = {
            'id': 999,
            'customer_name': 'Test Customer',
            'items_summary': '2x Burger, 1x Fries',
            'total': 350.00,
            'delivery_type': 'Delivery',
            'payment_type': 'Cash'
        }
        
        # Initialize Twilio notifications
        twilio_notifications = TwilioNotifications()
        
        print(f"\n📤 Sending WhatsApp notification...")
        success, result = twilio_notifications.send_new_order_notification(
            vendor.phone, 
            test_order_data
        )
        
        if success:
            print(f"✅ WhatsApp notification sent successfully!")
            print(f"📋 Message SID: {result}")
            print(f"📱 Sent to: {vendor.phone}")
            print(f"\n💡 Check vendor's WhatsApp for the message")
            return True
        else:
            print(f"❌ WhatsApp notification failed!")
            print(f"🔍 Error: {result}")
            return False

if __name__ == "__main__":
    print("🚀 LocalConnect WhatsApp Notification Test")
    print("Testing: Customer order → Vendor WhatsApp notification")
    print("=" * 60)
    
    try:
        success = test_whatsapp_notification()
        
        if success:
            print("\n🎉 WhatsApp notification test completed!")
            print("💡 If vendor didn't receive message:")
            print("   1. Check Twilio WhatsApp sandbox setup")
            print("   2. Verify vendor phone number format (+91xxxxxxxxxx)")
            print("   3. Check Twilio console for delivery status")
            sys.exit(0)
        else:
            print("\n❌ WhatsApp notification test failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)