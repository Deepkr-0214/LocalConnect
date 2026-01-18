#!/usr/bin/env python
"""
Debug script to test Twilio SMS and WhatsApp notifications
"""

from twilio.rest import Client
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twilio_connection():
    """Test Twilio connection and credentials"""
    
    print("🔍 TWILIO DEBUG TEST")
    print("=" * 50)
    
    # Twilio credentials from .env
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    sms_number = os.getenv('TWILIO_PHONE_NUMBER')
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    print(f"Account SID: {account_sid}")
    print(f"SMS Number: {sms_number}")
    print(f"WhatsApp Number: {whatsapp_number}")
    print()
    
    if not all([account_sid, auth_token, sms_number, whatsapp_number]):
        print("❌ Missing Twilio credentials in .env file")
        return
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        print("✅ Twilio client initialized successfully")
        
        # Test account info
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Account status: {account.status}")
        print(f"✅ Account name: {account.friendly_name}")
        print()
        
        # Get test phone number (replace with actual test number)
        test_phone = input("Enter test phone number (with +91 prefix): ").strip()
        
        if not test_phone.startswith('+91'):
            if test_phone.startswith('91'):
                test_phone = f"+{test_phone}"
            else:
                test_phone = f"+91{test_phone.lstrip('0')}"
        
        print(f"Testing with phone number: {test_phone}")
        print()
        
        # Test SMS
        print("📱 Testing SMS...")
        try:
            sms_message = client.messages.create(
                body="🧪 TEST SMS from LocalConnect! Your SMS notifications are working correctly.",
                from_=sms_number,
                to=test_phone
            )
            print(f"✅ SMS sent successfully! SID: {sms_message.sid}")
            print(f"✅ SMS status: {sms_message.status}")
        except Exception as e:
            print(f"❌ SMS failed: {e}")
        
        print()
        
        # Test WhatsApp
        print("💬 Testing WhatsApp...")
        try:
            whatsapp_message = client.messages.create(
                body="🧪 TEST WHATSAPP from LocalConnect! Your WhatsApp notifications are working correctly.",
                from_=whatsapp_number,
                to=f"whatsapp:{test_phone}"
            )
            print(f"✅ WhatsApp sent successfully! SID: {whatsapp_message.sid}")
            print(f"✅ WhatsApp status: {whatsapp_message.status}")
        except Exception as e:
            print(f"❌ WhatsApp failed: {e}")
        
        print()
        print("🔍 TROUBLESHOOTING TIPS:")
        print("1. For trial accounts, verify phone numbers in Twilio console")
        print("2. For WhatsApp, join sandbox: https://wa.me/14155238886?text=join%20[sandbox-name]")
        print("3. Check account balance for paid accounts")
        print("4. Ensure phone number format is +91XXXXXXXXXX")
        
    except Exception as e:
        print(f"❌ Twilio connection failed: {e}")
        print()
        print("🔍 POSSIBLE ISSUES:")
        print("1. Invalid Account SID or Auth Token")
        print("2. Network connectivity issues")
        print("3. Twilio account suspended or restricted")

if __name__ == '__main__':
    test_twilio_connection()