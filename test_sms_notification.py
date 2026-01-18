#!/usr/bin/env python3
"""
Test SMS notification functionality
"""

from utils.twilio_notifications import TwilioNotifications
from datetime import datetime
import pytz

def test_sms_notifications():
    """Test SMS notifications for both vendor and customer"""
    
    # Initialize Twilio notifications
    twilio = TwilioNotifications()
    ist = pytz.timezone('Asia/Kolkata')
    
    # Test phone numbers (replace with actual test numbers)
    test_vendor_phone = "+919876543210"  # Replace with actual vendor phone
    test_customer_phone = "+919876543211"  # Replace with actual customer phone
    
    print("Testing SMS Notifications...")
    print("=" * 50)
    
    # Test 1: New Order Notification to Vendor
    print("\n1. Testing New Order Notification to Vendor...")
    order_data = {
        'id': 123,
        'customer_name': 'John Doe',
        'items_summary': '2x Burger, 1x Fries',
        'total': 250,
        'delivery_type': 'Delivery',
        'payment_type': 'Online'
    }
    
    success, result = twilio.send_new_order_notification(test_vendor_phone, order_data)
    print(f"Result: {success} - {result}")
    
    # Test 2: Order Status Notification to Customer
    print("\n2. Testing Order Status Notification to Customer...")
    customer_order_data = {
        'id': 123,
        'vendor_name': 'Test Restaurant'
    }
    
    success, result = twilio.send_order_status_notification(test_customer_phone, customer_order_data, 'preparing')
    print(f"Result: {success} - {result}")
    
    # Test 3: SMS Confirmation
    print("\n3. Testing SMS Confirmation...")
    test_message = f"Test SMS from LocalConnect! Time: {datetime.now(ist).strftime('%I:%M %p')}"
    success, result = twilio.send_confirmation_sms(test_customer_phone, test_message)
    print(f"Result: {success} - {result}")
    
    print("\n" + "=" * 50)
    print("SMS Testing Complete!")

if __name__ == "__main__":
    test_sms_notifications()