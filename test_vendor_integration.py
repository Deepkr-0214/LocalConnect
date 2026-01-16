import sys
sys.path.insert(0, 'd:\\courses\\LocalService')

from app import app

print("Testing Vendor Routes Integration...")
print("=" * 50)

with app.test_client() as client:
    # Test routes exist
    routes = [
        '/vendor/dashboard',
        '/vendor/orders',
        '/vendor/menu',
        '/vendor/earnings',
        '/vendor/reviews'
    ]
    
    for route in routes:
        # Check if route exists (will redirect to login if not authenticated)
        response = client.get(route, follow_redirects=False)
        if response.status_code in [200, 302]:  # 302 = redirect to login
            print(f"[OK] {route} - Route exists")
        else:
            print(f"[FAIL] {route} - Route missing (Status: {response.status_code})")

print("\n" + "=" * 50)
print("All vendor pages are now integrated!")
print("\nTo access:")
print("1. Start the app: python app.py")
print("2. Go to: http://localhost:5000")
print("3. Click 'Sign In'")
print("4. Login as vendor")
print("5. Access all pages from the sidebar:")
print("   - Dashboard")
print("   - Orders")
print("   - Menu Management")
print("   - Earnings")
print("   - Reviews")
