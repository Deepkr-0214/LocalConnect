class EnhancedNotifications:
    def __init__(self):
        pass

    def format_phone(self, phone):
        return str(phone)

    def send_whatsapp_text(self, phone_number, message):
        return "MOCK_SID"

    def send_dual_notification(self, phone_number, message, variables=None):
        return {'sms': 'MOCK_SID', 'whatsapp': 'MOCK_SID', 'errors': []}

    def notify_customer_order_placed(self, phone, order_data):
        return self.send_dual_notification(phone, "Mock order placed")

    def notify_vendor_new_order(self, phone, order_data):
        return self.send_dual_notification(phone, "Mock new order")

    def notify_customer_order_status(self, phone, order_data, status):
        return self.send_dual_notification(phone, f"Mock status: {status}")

    def notify_vendor_order_completed(self, phone, order_data):
        return self.send_dual_notification(phone, "Mock order completed")

    def notify_admin_contact_form(self, phone, data):
        print(f"DEBUG: Mock notification for contact form: {data}")
        return self.send_dual_notification(phone, "Mock contact form")