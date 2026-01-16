"""
LOCALCONNECT-VENDOR-SHOP - COMPLETE INTEGRATION TEST
This script verifies all pages are properly integrated with backend data
"""

from app import app
from models import db, Order, MenuItem, Vendor
from datetime import date
from sqlalchemy import func, and_

print("\n" + "="*60)
print("LOCALCONNECT-VENDOR-SHOP - INTEGRATION TEST")
print("="*60 + "\n")

with app.app_context():
    vendor_id = 1
    today = date.today()
    
    # Test 1: Database Connection
    print("[TEST 1] Database Connection")
    try:
        Order.query.first()
        print("  [OK] Database connected successfully")
    except Exception as e:
        print(f"  [FAIL] Database error: {e}")
        exit(1)
    
    # Test 2: Dashboard Data
    print("\n[TEST 2] Dashboard Data Integration")
    todays_orders = Order.query.filter(and_(Order.vendor_id == vendor_id, func.date(Order.date_posted) == today)).count()
    pending_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    todays_earnings = db.session.query(func.sum(Order.total)).filter(and_(Order.vendor_id == vendor_id, func.date(Order.date_posted) == today, Order.status == 'Completed')).scalar() or 0.0
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(and_(Order.vendor_id == vendor_id, Order.review_rating.isnot(None))).scalar() or 0.0
    
    print(f"  [OK] Today's Orders: {todays_orders}")
    print(f"  [OK] Pending Orders: {pending_orders}")
    print(f"  [OK] Today's Earnings: Rs.{todays_earnings}")
    print(f"  [OK] Average Rating: {round(avg_rating, 1)}")
    
    # Test 3: Menu Items
    print("\n[TEST 3] Menu Management Integration")
    menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    print(f"  [OK] Menu Items Count: {len(menu_items)}")
    if len(menu_items) == 0:
        print("  [INFO] No menu items yet (vendor needs to add items)")
    
    # Test 4: Orders List
    print("\n[TEST 4] Orders Page Integration")
    all_orders = Order.query.filter_by(vendor_id=vendor_id).all()
    print(f"  [OK] Total Orders: {len(all_orders)}")
    for order in all_orders[:3]:
        print(f"    - Order #{order.id}: {order.status} - Rs.{order.total_price}")
    
    # Test 5: Templates
    print("\n[TEST 5] Template Files")
    import os
    templates = ['base.html', 'dashboard.html', 'orders.html', 'menu.html', 'earnings_simple.html', 'reviews_system.html', 'settings.html']
    for template in templates:
        path = os.path.join('templates', template)
        if os.path.exists(path):
            print(f"  [OK] {template}")
        else:
            print(f"  [FAIL] {template} MISSING")
    
    # Test 6: Static Files
    print("\n[TEST 6] Static Files (CSS/JS)")
    css_files = ['base.css', 'dashboard.css', 'orders.css', 'menu.css', 'earnings.css', 'reviews_system.css']
    js_files = ['menu.js', 'orders.js']
    
    for css in css_files:
        path = os.path.join('static', 'css', css)
        if os.path.exists(path):
            print(f"  [OK] css/{css}")
        else:
            print(f"  [FAIL] css/{css} MISSING")
    
    for js in js_files:
        path = os.path.join('static', 'js', js)
        if os.path.exists(path):
            print(f"  [OK] js/{js}")
        else:
            print(f"  [FAIL] js/{js} MISSING")
    
    # Test 7: Routes
    print("\n[TEST 7] Flask Routes")
    routes = {
        '/': 'Dashboard',
        '/orders': 'Orders Page',
        '/menu': 'Menu Management',
        '/earnings': 'Earnings Page',
        '/reviews': 'Reviews Page',
        '/add_item': 'Add Menu Item',
        '/update_order/<int:order_id>': 'Update Order'
    }
    
    app_routes = [str(r) for r in app.url_map.iter_rules()]
    for route, name in routes.items():
        if any(route in r for r in app_routes):
            print(f"  [OK] {route} -> {name}")
        else:
            print(f"  [FAIL] {route} -> {name} MISSING")

print("\n" + "="*60)
print("INTEGRATION TEST COMPLETE")
print("="*60)
print("\nTo start the server:")
print("  python app.py")
print("\nAccess at: http://localhost:5001")
print("\n" + "="*60 + "\n")
