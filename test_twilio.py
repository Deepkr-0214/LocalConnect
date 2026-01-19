from twilio.rest import Client

# Test the exact configuration provided
account_sid = 'AC5d75a431c084b48b403bbf42add8d9f0'
auth_token = '14e8146b67204a153dc28f6cc60b5b1b'
client = Client(account_sid, auth_token)

# Test SMS
try:
    sms = client.messages.create(
        body="Test SMS from LocalConnect - Order notifications working!",
        from_='+15419453187',
        to='+919939373128'
    )
    print(f"SMS sent: {sms.sid}")
except Exception as e:
    print(f"SMS failed: {e}")

# Test WhatsApp
try:
    whatsapp = client.messages.create(
        from_='whatsapp:+14155238886',
        content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
        content_variables='{"1":"Order #123","2":"Pizza Palace"}',
        to='whatsapp:+919939373128'
    )
    print(f"WhatsApp sent: {whatsapp.sid}")
except Exception as e:
    print(f"WhatsApp failed: {e}")

print("Test complete!")