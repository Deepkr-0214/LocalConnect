from twilio.rest import Client
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TwilioNotifications:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.sms_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.client = Client(self.account_sid, self.auth_token)
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def send_new_order_notification(self, vendor_phone, order_data):
        """Send both WhatsApp and SMS notifications to vendor when new order is placed"""
        whatsapp_success = False
        sms_success = False
        
        # Send WhatsApp notification
        try:
            if not vendor_phone.startswith('whatsapp:'):
                whatsapp_phone = f"whatsapp:{vendor_phone}"
            else:
                whatsapp_phone = vendor_phone

            message_body = f"""🔔 NEW ORDER ALERT!

Order #{order_data['id']}
Customer: {order_data['customer_name']}
Items: {order_data['items_summary']}
Total: ₹{order_data['total']}
Type: {order_data['delivery_type']}
Payment: {order_data['payment_type']}

Reply ACCEPT {order_data['id']} or REJECT {order_data['id']} [reason]

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""

            message = self.client.messages.create(
                body=message_body,
                from_=self.whatsapp_number,
                to=whatsapp_phone
            )
            whatsapp_success = True
            print(f"WhatsApp notification sent to {vendor_phone}: {message.sid}")
        except Exception as e:
            print(f"WhatsApp notification failed for {vendor_phone}: {e}")
        
        # Send SMS notification
        try:
            sms_phone = vendor_phone.replace('whatsapp:', '') if vendor_phone.startswith('whatsapp:') else vendor_phone
            
            sms_body = f"""NEW ORDER #{order_data['id']}
Customer: {order_data['customer_name']}
Items: {order_data['items_summary']}
Total: Rs{order_data['total']}
Type: {order_data['delivery_type']}
Payment: {order_data['payment_type']}
Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""

            sms_message = self.client.messages.create(
                body=sms_body,
                from_=self.sms_number,
                to=sms_phone
            )
            sms_success = True
            print(f"SMS notification sent to {vendor_phone}: {sms_message.sid}")
        except Exception as e:
            print(f"SMS notification failed for {vendor_phone}: {e}")
        
        return whatsapp_success or sms_success, f"WhatsApp: {whatsapp_success}, SMS: {sms_success}"
    
    def send_order_status_notification(self, customer_phone, order_data, status):
        """Send both WhatsApp and SMS notifications to customer when order status changes"""
        whatsapp_success = False
        sms_success = False
        
        status_messages = {
            'preparing': f"🍳 Your order #{order_data['id']} is being prepared!\n\nVendor: {order_data['vendor_name']}\nEstimated time: 15-20 mins",
            'ready': f"✅ Your order #{order_data['id']} is ready for pickup!\n\nVendor: {order_data['vendor_name']}\nPlease collect your order.",
            'out_for_delivery': f"🚚 Your order #{order_data['id']} is out for delivery!\n\nVendor: {order_data['vendor_name']}\nEstimated delivery: 10-15 mins",
            'Completed': f"🎉 Order #{order_data['id']} completed!\n\nThank you for choosing {order_data['vendor_name']}!\nPlease rate your experience.",
            'Rejected': f"❌ Order #{order_data['id']} was rejected.\n\nReason: {order_data.get('rejection_reason', 'Not specified')}\nRefund will be processed if applicable."
        }
        
        message_body = status_messages.get(status, f"Order #{order_data['id']} status updated to: {status}")
        time_stamp = f"\n\nTime: {datetime.now(self.ist).strftime('%I:%M %p')}"
        
        # Send WhatsApp notification
        try:
            whatsapp_phone = f"whatsapp:{customer_phone}"
            whatsapp_message = self.client.messages.create(
                body=message_body + time_stamp,
                from_=self.whatsapp_number,
                to=whatsapp_phone
            )
            whatsapp_success = True
            print(f"WhatsApp status notification sent to customer {customer_phone}: {whatsapp_message.sid}")
        except Exception as e:
            print(f"Error sending WhatsApp status notification: {e}")
        
        # Send SMS notification
        try:
            sms_phone = customer_phone.replace('whatsapp:', '') if customer_phone.startswith('whatsapp:') else customer_phone
            sms_message = self.client.messages.create(
                body=message_body + time_stamp,
                from_=self.sms_number,
                to=sms_phone
            )
            sms_success = True
            print(f"SMS status notification sent to customer {customer_phone}: {sms_message.sid}")
        except Exception as e:
            print(f"Error sending SMS status notification: {e}")
        
        return whatsapp_success or sms_success, f"WhatsApp: {whatsapp_success}, SMS: {sms_success}"
    
    def process_vendor_whatsapp_reply(self, from_number, message_body):
        """Process WhatsApp replies from vendors to accept/reject orders"""
        try:
            message_body = message_body.strip().upper()
            print(f"Processing WhatsApp reply from {from_number}: {message_body}")

            if message_body.startswith('ACCEPT'):
                parts = message_body.split(' ', 1)
                if len(parts) >= 2:
                    order_id = parts[1].strip()
                    return 'accept', order_id, None

            elif message_body.startswith('REJECT'):
                parts = message_body.split(' ', 2)
                if len(parts) >= 2:
                    order_id = parts[1].strip()
                    reason = parts[2] if len(parts) > 2 else "No reason provided"
                    return 'reject', order_id, reason

            return None, None, None

        except Exception as e:
            print(f"Error processing WhatsApp reply: {e}")
            return None, None, None

    def send_confirmation_whatsapp(self, phone_number, message):
        """Send confirmation WhatsApp message"""
        try:
            whatsapp_phone = f"whatsapp:{phone_number}"
            message = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=whatsapp_phone
            )
            return True, message.sid
        except Exception as e:
            print(f"Error sending confirmation WhatsApp: {e}")
            return False, str(e)
    
    def send_confirmation_sms(self, phone_number, message):
        """Send confirmation SMS message"""
        try:
            sms_phone = phone_number.replace('whatsapp:', '') if phone_number.startswith('whatsapp:') else phone_number
            sms_message = self.client.messages.create(
                body=message,
                from_=self.sms_number,
                to=sms_phone
            )
            return True, sms_message.sid
        except Exception as e:
            print(f"Error sending confirmation SMS: {e}")
            return False, str(e)
