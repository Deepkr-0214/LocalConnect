from twilio.rest import Client
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnhancedNotifications:
    """Enhanced notification system with comprehensive SMS and WhatsApp support for both customers and vendors"""
    
    def __init__(self):
        # Use environment variables from .env file
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.sms_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.ist = pytz.timezone('Asia/Kolkata')
            print(f"✅ Twilio client initialized - SMS: {self.sms_number}, WhatsApp: {self.whatsapp_number}")
        except Exception as e:
            print(f"❌ Failed to initialize Twilio client: {e}")
            self.client = None
        self.notification_types = {
            'new_order': 'New Order Received',
            'order_accepted': 'Order Accepted',
            'order_rejected': 'Order Rejected', 
            'order_preparing': 'Order Being Prepared',
            'order_ready': 'Order Ready',
            'order_out_for_delivery': 'Order Out for Delivery',
            'order_completed': 'Order Completed',
            'payment_received': 'Payment Received',
            'customer_registered': 'Welcome to LocalConnect',
            'vendor_registered': 'Vendor Account Created'
        }
    
    def send_dual_notification(self, phone_number, message, notification_type="general"):
        """Send both SMS and WhatsApp notifications"""
        results = {'sms': False, 'whatsapp': False, 'errors': []}
        
        if not self.client:
            results['errors'].append("Twilio client not initialized")
            return results
        
        if not phone_number:
            results['errors'].append("Phone number is empty")
            return results
        
        # Format phone number properly
        clean_phone = phone_number.replace('whatsapp:', '') if phone_number.startswith('whatsapp:') else phone_number
        if not clean_phone.startswith('+91'):
            if clean_phone.startswith('91'):
                clean_phone = f"+{clean_phone}"
            else:
                clean_phone = f"+91{clean_phone.lstrip('0')}"
        
        print(f"📤 Sending dual notification to {clean_phone}")
        
        # Send SMS
        try:
            print(f"Sending SMS to: {clean_phone}")
            sms_msg = self.client.messages.create(
                body=message,
                from_=self.sms_number,
                to=clean_phone
            )
            results['sms'] = True
            results['sms_sid'] = sms_msg.sid
            print(f"✅ SMS sent: {sms_msg.sid}")
        except Exception as e:
            error_msg = f"SMS failed: {str(e)}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        # Send WhatsApp
        try:
            whatsapp_phone = f"whatsapp:{clean_phone}"
            print(f"Sending WhatsApp to: {whatsapp_phone}")
            
            whatsapp_msg = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=whatsapp_phone
            )
            results['whatsapp'] = True
            results['whatsapp_sid'] = whatsapp_msg.sid
            print(f"✅ WhatsApp sent: {whatsapp_msg.sid}")
        except Exception as e:
            error_msg = f"WhatsApp failed: {str(e)}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        return results
    
    def notify_customer_order_placed(self, customer_phone, order_data):
        """Notify customer that their order has been placed"""
        message = f"""🛒 ORDER PLACED SUCCESSFULLY!

Order #{order_data['id']}
Vendor: {order_data['vendor_name']}
Items: {order_data['items_summary']}
Total: ₹{order_data['total']}
Payment: {order_data['payment_type']}

Your order is being sent to the vendor for confirmation.
You'll receive updates as your order progresses.

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        return self.send_dual_notification(customer_phone, message, 'order_placed')
    
    def notify_vendor_new_order(self, vendor_phone, order_data):
        """Enhanced vendor notification for new orders"""
        message = f"""🔔 NEW ORDER ALERT!

Order #{order_data['id']}
Customer: {order_data['customer_name']}
Phone: {order_data.get('customer_phone', 'N/A')}
Items: {order_data['items_summary']}
Total: ₹{order_data['total']}
Type: {order_data['delivery_type']}
Payment: {order_data['payment_type']}

Reply ACCEPT {order_data['id']} or REJECT {order_data['id']} [reason]

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        return self.send_dual_notification(vendor_phone, message, 'new_order')
    
    def notify_customer_order_status(self, customer_phone, order_data, status):
        """Enhanced customer notifications for order status changes"""
        status_messages = {
            'accepted': f"✅ ORDER ACCEPTED!\n\nOrder #{order_data['id']} has been accepted by {order_data['vendor_name']}!\nYour order is now being prepared.\n\nEstimated preparation time: 15-20 minutes",

            'preparing': f"🍳 ORDER BEING PREPARED!\n\nOrder #{order_data['id']} is now being prepared by {order_data['vendor_name']}.\n\nEstimated time: 15-20 minutes\nWe'll notify you when it's ready!",

            'ready': f"✅ ORDER READY FOR PICKUP!\n\nOrder #{order_data['id']} is ready!\nVendor: {order_data['vendor_name']}\n\nPlease collect your order at your earliest convenience.",

            'out_for_delivery': f"🚚 ORDER OUT FOR DELIVERY!\n\nOrder #{order_data['id']} is on its way!\nVendor: {order_data['vendor_name']}\n\nEstimated delivery: 10-15 minutes\nPlease be available to receive your order.",

            'Completed': f"🎉 ORDER DELIVERED!\n\nOrder #{order_data['id']} has been completed!\nTotal: ₹{order_data['total']}\n\nThank you for choosing {order_data['vendor_name']}!\nPlease rate your experience in the app.",

            'Rejected': f"❌ ORDER REJECTED\n\nOrder #{order_data['id']} was rejected by {order_data['vendor_name']}.\n\nReason: {order_data.get('rejection_reason', 'Not specified')}\nRefund will be processed if payment was made online."
        }
        
        message = status_messages.get(status, f"Order #{order_data['id']} status updated to: {status}")
        message += f"\n\nTime: {datetime.now(self.ist).strftime('%I:%M %p')}"
        
        return self.send_dual_notification(customer_phone, message, f'order_{status}')
    
    def notify_vendor_order_completed(self, vendor_phone, order_data):
        """Notify vendor when order is completed"""
        message = f"""🎉 ORDER COMPLETED!

Order #{order_data['id']} has been completed!
Customer: {order_data['customer_name']}
Total: ₹{order_data['total']}

Earnings have been added to your account.
Thank you for using LocalConnect!

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        return self.send_dual_notification(vendor_phone, message, 'order_completed')
    
    def notify_customer_welcome(self, customer_phone, customer_name):
        """Welcome notification for new customers"""
        message = f"""🎉 WELCOME TO LOCALCONNECT!

Hi {customer_name}!

Thank you for joining LocalConnect - your local food delivery platform.

✅ Browse local restaurants
✅ Order your favorite food
✅ Track orders in real-time
✅ Rate and review

Start exploring delicious food near you!

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        return self.send_dual_notification(customer_phone, message, 'customer_registered')
    
    def notify_vendor_welcome(self, vendor_phone, business_name):
        """Welcome notification for new vendors"""
        message = f"""🏪 WELCOME TO LOCALCONNECT!

Hi {business_name}!

Your vendor account has been created successfully!

✅ Manage your menu
✅ Receive orders instantly
✅ Track earnings
✅ Respond to reviews

You'll receive order notifications via SMS and WhatsApp.
Reply ACCEPT [order_id] or REJECT [order_id] [reason] to manage orders.

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        return self.send_dual_notification(vendor_phone, message, 'vendor_registered')
    
    def notify_payment_confirmation(self, customer_phone, vendor_phone, order_data):
        """Notify both customer and vendor about successful payment"""
        # Customer notification
        customer_message = f"""💳 PAYMENT CONFIRMED!

Order #{order_data['id']}
Amount: ₹{order_data['total']}
Vendor: {order_data['vendor_name']}

Your payment has been processed successfully.
Order is being sent to vendor for confirmation.

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        # Vendor notification
        vendor_message = f"""💰 PAYMENT RECEIVED!

Order #{order_data['id']}
Customer: {order_data['customer_name']}
Amount: ₹{order_data['total']}
Payment: CONFIRMED

Order is ready for processing.
Reply ACCEPT {order_data['id']} to confirm.

Time: {datetime.now(self.ist).strftime('%I:%M %p')}"""
        
        customer_result = self.send_dual_notification(customer_phone, customer_message, 'payment_received')
        vendor_result = self.send_dual_notification(vendor_phone, vendor_message, 'payment_received')
        
        return {
            'customer': customer_result,
            'vendor': vendor_result
        }
    
    def send_bulk_notification(self, phone_numbers, message, notification_type="bulk"):
        """Send notifications to multiple recipients"""
        results = []
        for phone in phone_numbers:
            result = self.send_dual_notification(phone, message, notification_type)
            result['phone'] = phone
            results.append(result)
        return results
    
    def get_notification_status(self, message_sid):
        """Get the status of a sent message"""
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
        except Exception as e:
            return {'error': str(e)}