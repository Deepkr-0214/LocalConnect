# Twilio SMS Notification System Setup Guide

## 🚀 Quick Start

Your Twilio SMS notification system is now integrated! Here's how it works:

### 📱 Notification Flow

1. **Customer places order** → SMS sent to vendor
2. **Vendor replies via SMS** → Order accepted/rejected automatically  
3. **Vendor updates status** → SMS sent to customer
4. **Customer receives order** → Completion SMS sent to both

---

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Twilio Configuration
Your credentials are already configured:
- **Account SID**: AC712fd23c15ce55c8b6abfd9a85cfc3a6
- **Auth Token**: c8a2b319b29346a39336582fef3fe024
- **Phone Number**: +17752786168

### 3. Configure Webhook (Important!)
To receive SMS replies from vendors, configure your Twilio webhook:

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your number: +12569527132
4. In "Messaging" section, set webhook URL to:
   ```
   https://yourdomain.com/api/twilio/webhook
   ```
5. Set HTTP method to: **POST**
6. Save configuration

### 4. Test the System
```bash
python test_twilio.py
```

---

## 📋 SMS Commands for Vendors

Vendors can reply to order notifications with:

### Accept Order
```
ACCEPT 12345
```

### Reject Order  
```
REJECT 12345 Out of ingredients
```

---

## 🔄 Notification Examples

### New Order (to Vendor)
```
🔔 NEW ORDER ALERT!

Order #12345
Customer: John Doe
Items: Burger x2, Fries x1
Total: ₹450
Type: home_delivery
Payment: online

Reply:
- ACCEPT 12345 to accept
- REJECT 12345 [reason] to reject

Time: 2:30 PM
```

### Status Update (to Customer)
```
🍳 Your order #12345 is being prepared!

Vendor: Pizza Palace
Estimated time: 15-20 mins
```

### Order Ready (to Customer)
```
✅ Your order #12345 is ready for pickup!

Vendor: Pizza Palace
Please collect your order.
```

### Out for Delivery (to Customer)
```
🚚 Your order #12345 is out for delivery!

Vendor: Pizza Palace
Estimated delivery: 10-15 mins
```

### Order Completed (to Customer)
```
🎉 Order #12345 completed!

Thank you for choosing Pizza Palace!
Please rate your experience.
```

---

## 🛠 API Endpoints

### Test SMS Notification
```javascript
POST /api/twilio/test-notification
// Sends test SMS to logged-in vendor
```

### SMS Status Update
```javascript
POST /api/vendor/sms-status-update
{
  "order_id": 12345,
  "status": "ready"
}
// Updates order status and sends SMS to customer
```

### Customer Order Received
```javascript
POST /api/customer/sms-order-received
{
  "order_id": 12345
}
// Marks order complete and sends confirmation SMS
```

### Webhook Handler
```javascript
POST /api/twilio/webhook
// Handles incoming SMS from vendors
// Automatically processes ACCEPT/REJECT commands
```

---

## 🔍 Integration Points

### Order Creation (app.py)
- Automatically sends SMS to vendor when order is placed
- Includes order details and reply instructions

### Status Updates (app.py)  
- Sends SMS to customer when vendor updates order status
- Includes estimated times and vendor information

### SMS Replies (webhook)
- Processes vendor SMS replies automatically
- Updates order status in database
- Sends confirmations to both parties

---

## 🧪 Testing Checklist

- [ ] Install Twilio package: `pip install twilio`
- [ ] Run test script: `python test_twilio.py`
- [ ] Configure webhook URL in Twilio console
- [ ] Test order creation → vendor SMS
- [ ] Test vendor SMS reply → order acceptance
- [ ] Test status updates → customer SMS
- [ ] Test order completion flow

---

## 🚨 Important Notes

1. **Phone Numbers**: Ensure all vendor and customer phone numbers include country code (+91 for India)

2. **Webhook URL**: Must be publicly accessible HTTPS URL for production

3. **SMS Costs**: Each SMS costs money - monitor usage in Twilio console

4. **Rate Limits**: Twilio has rate limits - implement queuing for high volume

5. **Error Handling**: All SMS failures are logged but don't break the order flow

---

## 🔧 Troubleshooting

### SMS Not Received
- Check phone number format (+country code)
- Verify Twilio account balance
- Check Twilio logs in console

### Webhook Not Working
- Ensure URL is publicly accessible
- Check webhook configuration in Twilio
- Verify HTTPS (required for production)

### Invalid SMS Commands
- Vendors receive help message for invalid formats
- Commands are case-insensitive
- Order ID must match exactly

---

## 📞 Support

For Twilio-specific issues:
- [Twilio Documentation](https://www.twilio.com/docs)
- [Twilio Console](https://console.twilio.com/)
- Check logs in Twilio console for delivery status