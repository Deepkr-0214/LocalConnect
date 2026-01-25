import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_chat():
    print("🚀 Starting Chatbot Verification...")
    
    session = requests.Session()
    
    # 1. Signup/Login as Customer
    print("1. Creating/Logging in Test Customer...")
    signup_data = {
        'full_name': 'Test Chat',
        'email': 'chat_test@example.com',
        'phone': '+919999988888',
        'password': 'password123',
        'confirm_password': 'password123'
    }
    
    # Try signup
    session.post(f"{BASE_URL}/customer/signup", data=signup_data)
    
    # Login
    login_data = {
        'role': 'customer',
        'username': 'chat_test@example.com',
        'password': 'password123'
    }
    r = session.post(f"{BASE_URL}/signin", data=login_data)
    
    if 'dashboard' not in r.url and 'customer' not in r.url:
        print("❌ Login failed. Check if server is running or credentials.")
        return

    print("✅ Login successful.")

    # 2. Test Search Intent
    print("\n2. Testing 'Find Biryani'...")
    r = session.post(f"{BASE_URL}/chat", json={'message': 'Find biryani'})
    data = r.json()
    print("Response:", data)
    
    if 'available shops' in data.get('reply', '').lower():
        print("✅ Food Search Working!")
    else:
        print("❌ Food Search Failed or No Shops Found.")

    # 3. Test Handoff Intent
    print("\n3. Testing 'Talk to support'...")
    r = session.post(f"{BASE_URL}/chat", json={'message': 'Talk to support'})
    data = r.json()
    print("Response:", data)
    
    if data.get('handoff') is True:
        print("✅ Handoff Logic Working!")
        with open("verify_result.txt", "w") as f:
            f.write("PASSED")
    else:
        print("❌ Handoff Logic Failed.")
        with open("verify_result.txt", "w") as f:
            f.write("FAILED")

    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    try:
        test_chat()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
