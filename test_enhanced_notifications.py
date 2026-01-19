#!/usr/bin/env python3
"""
Test script for Enhanced SMS & WhatsApp Notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.enhanced_notifications import EnhancedNotifications

def test_notifications():
    print("🧪 Testing Enhanced SMS & WhatsApp Notifications...")
    
    # Initialize notification system
    notifier = EnhancedNotifications()
    
    # Test phone numbers (replace with actual numbers for testing)
    test_customer_phone = "+919142359287"
    test_vendor_phone = "+919939373128"
    
    # Test order data
    test_order_data = {
        'id': 'TEST123',
        'customer_name': 'Test Customer',
        'vendor_name': 'Test Restaurant',
        'items_summary': '2x Burger, 1x Fries',
        'total': '299',
        'delivery_type': 'delivery',
        'payment_type': 'online'
    }
    
    print("\n📱 Testing Customer Order Placed Notification...")
    result1 = notifier.notify_customer_order_placed(test_customer_phone, test_order_data)
    print(f"Result: {result1}")
    
    print("\n🏪 Testing Vendor New Order Notification...")
    result2 = notifier.notify_vendor_new_order(test_vendor_phone, test_order_data)
    print(f"Result: {result2}")
    
    print("\n📋 Testing Order Status Update...")
    result3 = notifier.notify_customer_order_status(test_customer_phone, test_order_data, 'preparing')
    print(f"Result: {result3}")
    
    print("\n✅ Testing Order Completion...")
    result4 = notifier.notify_vendor_order_completed(test_vendor_phone, test_order_data)
    print(f"Result: {result4}")
    
    print("\n🎉 All tests completed!")
    print("Check your phone for SMS and WhatsApp messages.")

if __name__ == "__main__":
    test_notifications()