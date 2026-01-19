import os
from twilio.rest import Client
import json
from dotenv import load_dotenv

load_dotenv()

class EnhancedNotifications:
    def __init__(self):
        self.client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.content_sid = os.getenv('TWILIO_CONTENT_SID')

    def format_phone(self, phone):
        clean = str(phone).replace('whatsapp:', '').replace('+', '').replace(' ', '')
        if not clean.startswith('91'):
            clean = f"91{clean.lstrip('0')}"
        return f"+{clean}"

    def send_dual_notification(self, phone_number, message, variables=None):
        clean_phone = self.format_phone(phone_number)
        
        try:
            # Send SMS
            sms_result = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=clean_phone
            )
            
            # Send WhatsApp Template
            whatsapp_result = None
            if variables:
                whatsapp_result = self.client.messages.create(
                    from_=self.whatsapp_number,
                    content_sid=self.content_sid,
                    content_variables=json.dumps(variables),
                    to=f'whatsapp:{clean_phone}'
                )
            
            return f"SMS: {sms_result.sid}, WhatsApp: {whatsapp_result.sid if whatsapp_result else 'N/A'}"
        except Exception as e:
            return f"Error: {str(e)}"

    def notify_customer_order_placed(self, phone, order_data):
        message = f"Order #{order_data['id']} placed at {order_data['vendor_name']}. Total: ₹{order_data['total']}. We'll notify you when it's ready!"
        variables = {"1": order_data['vendor_name'], "2": f"Order #{order_data['id']}"}
        return self.send_dual_notification(phone, message, variables)

    def notify_vendor_new_order(self, phone, order_data):
        message = f"New Order #{order_data['id']} from {order_data['customer_name']}. Items: {order_data['items_summary']}. Total: ₹{order_data['total']}. Reply ACCEPT or REJECT."
        variables = {"1": order_data['customer_name'], "2": f"Order #{order_data['id']}"}
        return self.send_dual_notification(phone, message, variables)

    def notify_customer_order_status(self, phone, order_data, status):
        status_messages = {
            'accepted': f"Great! {order_data['vendor_name']} accepted your order #{order_data['id']}. Preparing now...",
            'preparing': f"Your order #{order_data['id']} is being prepared at {order_data['vendor_name']}. ETA: 20-30 mins",
            'ready': f"Order #{order_data['id']} is ready for pickup at {order_data['vendor_name']}!",
            'out_for_delivery': f"Your order #{order_data['id']} is out for delivery! Track your order.",
            'completed': f"Order #{order_data['id']} delivered! Thank you for choosing {order_data['vendor_name']}!",
            'rejected': f"Sorry, {order_data['vendor_name']} cannot fulfill order #{order_data['id']} right now."
        }
        
        message = status_messages.get(status, f"Order #{order_data['id']} status: {status}")
        variables = {"1": order_data['vendor_name'], "2": status.title()}
        return self.send_dual_notification(phone, message, variables)

    def notify_vendor_order_completed(self, phone, order_data):
        message = f"Order #{order_data['id']} completed! Earnings: ₹{order_data['total']} added to your account."
        variables = {"1": f"Order #{order_data['id']}", "2": f"₹{order_data['total']}"}
        return self.send_dual_notification(phone, message, variables)