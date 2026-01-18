#!/usr/bin/env python
"""
Check phone numbers in database and test notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db, Customer, Vendor
from utils.enhanced_notifications import EnhancedNotifications
from app import app

def check_phone_numbers():
    """Check phone numbers in database"""
    
    print("📱 PHONE NUMBER CHECK")
    print("=" * 50)
    
    with app.app_context():
        # Check customers
        customers = Customer.query.all()
        print(f"Found {len(customers)} customers:")
        for customer in customers:
            print(f"  {customer.full_name}: {customer.phone}")
        
        print()
        
        # Check vendors
        vendors = Vendor.query.all()
        print(f"Found {len(vendors)} vendors:")
        for vendor in vendors:
            print(f"  {vendor.business_name}: {vendor.phone}")
        
        print()
        
        # Test with first vendor if available
        if vendors:
            test_vendor = vendors[0]
            print(f"🧪 Testing notifications with vendor: {test_vendor.business_name}")
            print(f"Phone: {test_vendor.phone}")
            
            if test_vendor.phone:
                notifications = EnhancedNotifications()
                
                test_message = f"🧪 TEST from LocalConnect!\\n\\nHi {test_vendor.business_name},\\nThis is a test notification to verify your SMS and WhatsApp are working.\\n\\nIf you receive this, notifications are working correctly!"
                
                print("\\nSending test notification...")
                result = notifications.send_dual_notification(test_vendor.phone, test_message, 'test')
                
                print(f"\\nResults:")
                print(f"SMS Success: {result['sms']}")
                print(f"WhatsApp Success: {result['whatsapp']}")
                if result['errors']:
                    print(f"Errors: {result['errors']}")
            else:
                print("❌ Vendor has no phone number")
        else:
            print("❌ No vendors found in database")

if __name__ == '__main__':
    check_phone_numbers()