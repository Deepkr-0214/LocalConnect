import os
from dotenv import load_dotenv
from twilio.rest import Client
import sys

# Load environment variables
load_dotenv()

sid = os.getenv('TWILIO_ACCOUNT_SID')
token = os.getenv('TWILIO_AUTH_TOKEN')

if not sid or not token:
    print("Error: Missing credentials")
    sys.exit(1)

try:
    client = Client(sid, token)
    account = client.api.accounts(sid).fetch()
    print(f"Account Status: {account.status}")
    print(f"Account Type: {account.type}")
    
    if account.type == 'Trial':
        print("\nChecking Verified Caller IDs (Required for Trial Accounts)...")
        incoming_phone_numbers = client.incoming_phone_numbers.list(limit=20)
        outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20)
        
        print("\n--- Verified Destination Numbers (Outgoing Caller IDs) ---")
        if not outgoing_caller_ids:
            print("No verified numbers found! You can only send SMS to verified numbers in Trial mode.")
        else:
            for record in outgoing_caller_ids:
                print(f"- {record.phone_number} ({record.friendly_name})")
                
        print("\n--- Your Twilio Phone Numbers ---")
        if not incoming_phone_numbers:
             print("No purchased/assigned Twilio numbers found.")
        else:
            for record in incoming_phone_numbers:
                print(f"- {record.phone_number}")

except Exception as e:
    print(f"❌ Error: {e}")
