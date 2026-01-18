#!/usr/bin/env python3
"""
Test script for Twilio SMS notifications
Run this to test if SMS functionality is working
"""

from utils.twilio_notifications import TwilioNotifications
from datetime import datetime
import pytz

def test_twilio_setup():
    """Test basic Twilio setup and send a test SMS"""
    
    print("🧪 Testing Twilio SMS Setup...")
    print("=" * 50)
    
    # Initialize Twilio
    twilio = TwilioNotifications()
    
    # Test phone number (replace with your test number)
    test_phone = input("Enter your phone number to test (with country code, e.g., +919876543210): ").strip()
    
    if not test_phone:
        print("❌ No phone number provided")
        return
    
    # Test message
    test_message = f"""
🧪 LocalConnect SMS Test

This is a test message from your LocalConnect app.

✅ Twilio integration is working!
📱 SMS notifications are ready

Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')}
    """.strip()
    
    print(f"📤 Sending test SMS to {test_phone}...")
    
    try:
        success, result = twilio.send_confirmation_sms(test_phone, test_message)
        
        if success:
            print(f"✅ SMS sent successfully!")
            print(f"📋 Message SID: {result}")
        else:
            print(f"❌ SMS failed: {result}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def test_order_notification():
    """Test order notification format"""
    
    print("\n📋 Testing Order Notification Format...")
    print("=" * 50)
    
    # Sample order data
    sample_order = {
        'id': 12345,
        'customer_name': 'John Doe',
        'items_summary': 'Burger x2, Fries x1',
        'total': 450.00,
        'delivery_type': 'home_delivery',
        'payment_type': 'online'
    }
    
    twilio = TwilioNotifications()
    
    # Test vendor phone
    vendor_phone = input("Enter vendor phone number to test order notification: ").strip()
    
    if vendor_phone:
        print(f"📤 Sending order notification to {vendor_phone}...")
        success, result = twilio.send_new_order_notification(vendor_phone, sample_order)
        
        if success:
            print(f"✅ Order notification sent!")
            print(f"📋 Message SID: {result}")
        else:
            print(f"❌ Failed: {result}")

def test_sms_reply_processing():
    """Test SMS reply processing logic"""
    
    print("\n🔄 Testing SMS Reply Processing...")
    print("=" * 50)
    
    twilio = TwilioNotifications()
    
    test_messages = [
        "ACCEPT 12345",
        "REJECT 12345 Out of ingredients",
        "accept 67890",
        "reject 67890",
        "invalid message",
        "ACCEPT",
        "REJECT 111 Item not available"
    ]
    
    for msg in test_messages:
        action, order_id, reason = twilio.process_vendor_sms_reply("+1234567890", msg)
        print(f"📱 '{msg}' → Action: {action}, Order: {order_id}, Reason: {reason}")

if __name__ == "__main__":
    print("🚀 LocalConnect Twilio SMS Test Suite")
    print("=" * 50)
    
    while True:
        print("\nSelect test:")
        print("1. Basic SMS Test")
        print("2. Order Notification Test") 
        print("3. SMS Reply Processing Test")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            test_twilio_setup()
        elif choice == "2":
            test_order_notification()
        elif choice == "3":
            test_sms_reply_processing()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")