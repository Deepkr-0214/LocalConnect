import sys
sys.path.insert(0, 'd:\\courses\\LocalService')

from app import app

print("Testing All Vendor Pages Integration...")
print("=" * 60)

with app.test_client() as client:
    # Test all vendor routes
    routes = [
        ('/vendor/dashboard', 'Dashboard'),
        ('/vendor/orders', 'Orders'),
        ('/vendor/menu', 'Menu Management'),
        ('/vendor/earnings', 'Earnings'),
        ('/vendor/reviews', 'Reviews'),
        ('/vendor/settings', 'Settings')
    ]
    
    print("\n1. ROUTE AVAILABILITY CHECK:")
    print("-" * 60)
    all_routes_ok = True
    for route, name in routes:
        response = client.get(route, follow_redirects=False)
        if response.status_code in [200, 302]:
            print(f"[OK] {name:20} -> {route}")
        else:
            print(f"[FAIL] {name:20} -> {route} (Status: {response.status_code})")
            all_routes_ok = False
    
    print("\n2. STATIC FILES CHECK:")
    print("-" * 60)
    static_files = [
        ('css/vendor/base.css', 'Base CSS'),
        ('css/vendor/orders.css', 'Orders CSS'),
        ('css/vendor/menu.css', 'Menu CSS'),
        ('css/vendor/earnings.css', 'Earnings CSS'),
        ('css/vendor/reviews.css', 'Reviews CSS'),
        ('css/vendor/settings.css', 'Settings CSS'),
        ('js/vendor/orders.js', 'Orders JS'),
        ('js/vendor/menu.js', 'Menu JS'),
        ('js/vendor/reviews.js', 'Reviews JS'),
        ('js/vendor/settings.js', 'Settings JS')
    ]
    
    import os
    all_files_ok = True
    for file_path, name in static_files:
        full_path = os.path.join('d:\\courses\\LocalService\\static', file_path)
        if os.path.exists(full_path):
            print(f"[OK] {name:20} -> {file_path}")
        else:
            print(f"[FAIL] {name:20} -> {file_path} (Missing)")
            all_files_ok = False
    
    print("\n3. TEMPLATE FILES CHECK:")
    print("-" * 60)
    templates = [
        ('vendor/base.html', 'Base Template'),
        ('vendor/vendor_dashboard.html', 'Dashboard Template'),
        ('vendor/orders.html', 'Orders Template'),
        ('vendor/menu.html', 'Menu Template'),
        ('vendor/earnings.html', 'Earnings Template'),
        ('vendor/reviews.html', 'Reviews Template'),
        ('vendor/settings.html', 'Settings Template')
    ]
    
    all_templates_ok = True
    for template_path, name in templates:
        full_path = os.path.join('d:\\courses\\LocalService\\templates', template_path)
        if os.path.exists(full_path):
            print(f"[OK] {name:25} -> {template_path}")
        else:
            print(f"[FAIL] {name:25} -> {template_path} (Missing)")
            all_templates_ok = False
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Routes:    {'PASS' if all_routes_ok else 'FAIL'}")
    print(f"CSS/JS:    {'PASS' if all_files_ok else 'FAIL'}")
    print(f"Templates: {'PASS' if all_templates_ok else 'FAIL'}")
    
    if all_routes_ok and all_files_ok and all_templates_ok:
        print("\n[SUCCESS] All vendor pages are properly integrated!")
        print("\nTo test:")
        print("1. Run: python app.py")
        print("2. Go to: http://localhost:5000")
        print("3. Sign in as vendor")
        print("4. Navigate through all pages using sidebar")
    else:
        print("\n[WARNING] Some issues found. Check above for details.")
