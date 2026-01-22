"""
Sample Vendor Data Population Script
Creates test vendors for all 6 categories with menu items
"""

from app import app, db
from models.models import Vendor, MenuItem
from datetime import datetime

def create_sample_vendors():
    """Create sample vendors for each category"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("Creating Sample Vendors for All Categories")
        print("="*60 + "\n")
        
        # Sample vendors data
        vendors_data = [
            # Food & Restaurant Category
            {
                'business_name': 'Tasty Bites Restaurant',
                'email': 'food@test.com',
                'password': 'test123',
                'business_category': 'Food & Restaurant',
                'business_sub_category': 'Restaurant',
                'business_address': '123 MG Road, Delhi',
                'phone': '+919876543210',
                'latitude': 28.6139,
                'longitude': 77.2090,
                'shop_image': '🍽️',
                'is_open': True,
                'menu_items': [
                    {'name': 'Butter Chicken', 'price': 250, 'category': 'Main Course'},
                    {'name': 'Paneer Tikka', 'price': 180, 'category': 'Starter'},
                    {'name': 'Naan', 'price': 40, 'category': 'Bread'},
                    {'name': 'Dal Makhani', 'price': 150, 'category': 'Main Course'},
                ]
            },
            
            # Garage Category
            {
                'business_name': 'QuickFix Auto Garage',
                'email': 'garage@test.com',
                'password': 'test123',
                'business_category': 'Garage',
                'business_sub_category': '2-Wheeler',
                'business_address': '456 Service Road, Delhi',
                'phone': '+919876543211',
                'latitude': 28.6200,
                'longitude': 77.2100,
                'shop_image': '🔧',
                'is_open': True,
                'menu_items': [
                    {'name': 'Oil Change', 'price': 500, 'category': 'Maintenance'},
                    {'name': 'Brake Service', 'price': 800, 'category': 'Repair'},
                    {'name': 'Tire Replacement', 'price': 1500, 'category': 'Replacement'},
                    {'name': 'General Service', 'price': 1200, 'category': 'Service'},
                ]
            },
            {
                'business_name': 'City Car Care',
                'email': 'carcare@test.com',
                'password': 'test123',
                'business_category': 'Garage',
                'business_sub_category': '4-Wheeler',
                'business_address': '789 Auto Street, Delhi',
                'phone': '+919876543212',
                'latitude': 28.6250,
                'longitude': 77.2150,
                'shop_image': '🚗',
                'is_open': True,
                'menu_items': [
                    {'name': 'Full Service', 'price': 3000, 'category': 'Service'},
                    {'name': 'AC Repair', 'price': 2500, 'category': 'Repair'},
                    {'name': 'Wheel Alignment', 'price': 1000, 'category': 'Maintenance'},
                ]
            },
            
            # Electronics Category
            {
                'business_name': 'Mobile World',
                'email': 'electronics@test.com',
                'password': 'test123',
                'business_category': 'Electronics',
                'business_sub_category': 'Mobiles',
                'business_address': '321 Tech Park, Delhi',
                'phone': '+919876543213',
                'latitude': 28.6100,
                'longitude': 77.2200,
                'shop_image': '📱',
                'is_open': True,
                'menu_items': [
                    {'name': 'Samsung Galaxy S23', 'price': 65000, 'category': 'Smartphones'},
                    {'name': 'iPhone 14', 'price': 79000, 'category': 'Smartphones'},
                    {'name': 'OnePlus 11', 'price': 56000, 'category': 'Smartphones'},
                    {'name': 'Wireless Earbuds', 'price': 3500, 'category': 'Accessories'},
                ]
            },
            {
                'business_name': 'Home Appliances Hub',
                'email': 'appliances@test.com',
                'password': 'test123',
                'business_category': 'Electronics',
                'business_sub_category': 'Home Appliances',
                'business_address': '654 Market Road, Delhi',
                'phone': '+919876543214',
                'latitude': 28.6180,
                'longitude': 77.2120,
                'shop_image': '🏠',
                'is_open': True,
                'menu_items': [
                    {'name': 'LED TV 43"', 'price': 28000, 'category': 'Television'},
                    {'name': 'Washing Machine', 'price': 22000, 'category': 'Appliances'},
                    {'name': 'Refrigerator', 'price': 35000, 'category': 'Appliances'},
                ]
            },
            
            # Fashion Category
            {
                'business_name': 'Fashion Trends',
                'email': 'fashion@test.com',
                'password': 'test123',
                'business_category': 'Fashion',
                'business_sub_category': 'Ladies',
                'business_address': '987 Fashion Street, Delhi',
                'phone': '+919876543215',
                'latitude': 28.6150,
                'longitude': 77.2080,
                'shop_image': '👗',
                'is_open': True,
                'menu_items': [
                    {'name': 'Designer Kurti', 'price': 1200, 'category': 'Ethnic Wear'},
                    {'name': 'Saree', 'price': 2500, 'category': 'Ethnic Wear'},
                    {'name': 'Western Dress', 'price': 1800, 'category': 'Western Wear'},
                    {'name': 'Handbag', 'price': 800, 'category': 'Accessories'},
                ]
            },
            {
                'business_name': 'Gents Fashion Store',
                'email': 'gentsfashion@test.com',
                'password': 'test123',
                'business_category': 'Fashion',
                'business_sub_category': 'Gents',
                'business_address': '147 Style Avenue, Delhi',
                'phone': '+919876543216',
                'latitude': 28.6220,
                'longitude': 77.2050,
                'shop_image': '👔',
                'is_open': True,
                'menu_items': [
                    {'name': 'Formal Shirt', 'price': 1500, 'category': 'Formal Wear'},
                    {'name': 'Jeans', 'price': 1200, 'category': 'Casual Wear'},
                    {'name': 'Blazer', 'price': 3500, 'category': 'Formal Wear'},
                ]
            },
            
            # Grocery Category
            {
                'business_name': 'Fresh Vegetables Market',
                'email': 'grocery@test.com',
                'password': 'test123',
                'business_category': 'Grocery',
                'business_sub_category': 'Vegetables',
                'business_address': '258 Market Lane, Delhi',
                'phone': '+919876543217',
                'latitude': 28.6170,
                'longitude': 77.2110,
                'shop_image': '🥬',
                'is_open': True,
                'menu_items': [
                    {'name': 'Tomatoes (1kg)', 'price': 40, 'category': 'Vegetables'},
                    {'name': 'Potatoes (1kg)', 'price': 30, 'category': 'Vegetables'},
                    {'name': 'Onions (1kg)', 'price': 35, 'category': 'Vegetables'},
                    {'name': 'Spinach (bunch)', 'price': 20, 'category': 'Leafy Greens'},
                ]
            },
            {
                'business_name': 'Daily Dairy Products',
                'email': 'dairy@test.com',
                'password': 'test123',
                'business_category': 'Grocery',
                'business_sub_category': 'Dairy & Eggs',
                'business_address': '369 Dairy Road, Delhi',
                'phone': '+919876543218',
                'latitude': 28.6190,
                'longitude': 77.2130,
                'shop_image': '🥛',
                'is_open': True,
                'menu_items': [
                    {'name': 'Fresh Milk (1L)', 'price': 60, 'category': 'Dairy'},
                    {'name': 'Eggs (12 pcs)', 'price': 84, 'category': 'Eggs'},
                    {'name': 'Paneer (250g)', 'price': 100, 'category': 'Dairy'},
                    {'name': 'Curd (500g)', 'price': 40, 'category': 'Dairy'},
                ]
            },
            
            # Pharmacy Category
            {
                'business_name': 'City Pharmacy',
                'email': 'pharmacy@test.com',
                'password': 'test123',
                'business_category': 'Pharmacy',
                'business_sub_category': 'Chemist & Drug Medicine',
                'business_address': '741 Health Street, Delhi',
                'phone': '+919876543219',
                'latitude': 28.6160,
                'longitude': 77.2070,
                'shop_image': '💊',
                'is_open': True,
                'menu_items': [
                    {'name': 'Paracetamol 500mg', 'price': 20, 'category': 'General Medicine'},
                    {'name': 'Cough Syrup', 'price': 85, 'category': 'Cold & Flu'},
                    {'name': 'Vitamin C Tablets', 'price': 150, 'category': 'Supplements'},
                    {'name': 'Band-Aid (10 pcs)', 'price': 40, 'category': 'First Aid'},
                ]
            },
            {
                'business_name': 'Ayurvedic Wellness',
                'email': 'ayurvedic@test.com',
                'password': 'test123',
                'business_category': 'Pharmacy',
                'business_sub_category': 'Ayurvedic Medicine',
                'business_address': '852 Wellness Road, Delhi',
                'phone': '+919876543220',
                'latitude': 28.6210,
                'longitude': 77.2140,
                'shop_image': '🌿',
                'is_open': True,
                'menu_items': [
                    {'name': 'Chyawanprash', 'price': 250, 'category': 'Immunity'},
                    {'name': 'Triphala Churna', 'price': 120, 'category': 'Digestive'},
                    {'name': 'Ashwagandha Capsules', 'price': 300, 'category': 'Wellness'},
                ]
            },
        ]
        
        created_count = 0
        
        for vendor_data in vendors_data:
            # Check if vendor already exists
            existing = Vendor.query.filter_by(email=vendor_data['email']).first()
            if existing:
                print(f"⚠️  Vendor already exists: {vendor_data['business_name']} ({vendor_data['email']})")
                continue
            
            # Extract menu items
            menu_items_data = vendor_data.pop('menu_items', [])
            
            # Create vendor
            vendor = Vendor(
                business_name=vendor_data['business_name'],
                email=vendor_data['email'],
                business_category=vendor_data['business_category'],
                business_sub_category=vendor_data['business_sub_category'],
                business_address=vendor_data['business_address'],
                phone=vendor_data['phone'],
                latitude=vendor_data['latitude'],
                longitude=vendor_data['longitude'],
                shop_image=vendor_data.get('shop_image', '🏪'),
                is_open=vendor_data.get('is_open', True)
            )
            vendor.set_password(vendor_data['password'])
            
            db.session.add(vendor)
            db.session.flush()  # Get vendor ID
            
            # Create menu items
            for item_data in menu_items_data:
                menu_item = MenuItem(
                    vendor_id=vendor.id,
                    name=item_data['name'],
                    price=item_data['price'],
                    category=item_data['category'],
                    is_available=True
                )
                db.session.add(menu_item)
            
            created_count += 1
            print(f"✅ Created: {vendor.business_name} ({vendor.business_category} - {vendor.business_sub_category})")
            print(f"   Email: {vendor_data['email']} | Password: {vendor_data['password']}")
            print(f"   Menu Items: {len(menu_items_data)}")
            print()
        
        db.session.commit()
        
        print("="*60)
        print(f"✅ Successfully created {created_count} vendors!")
        print("="*60)
        print("\n📝 LOGIN CREDENTIALS:")
        print("-" * 60)
        print("All vendors use password: test123")
        print("-" * 60)
        print("\nVendor Emails by Category:")
        print("  Food & Restaurant: food@test.com")
        print("  Garage (2-Wheeler): garage@test.com")
        print("  Garage (4-Wheeler): carcare@test.com")
        print("  Electronics (Mobiles): electronics@test.com")
        print("  Electronics (Appliances): appliances@test.com")
        print("  Fashion (Ladies): fashion@test.com")
        print("  Fashion (Gents): gentsfashion@test.com")
        print("  Grocery (Vegetables): grocery@test.com")
        print("  Grocery (Dairy): dairy@test.com")
        print("  Pharmacy (Chemist): pharmacy@test.com")
        print("  Pharmacy (Ayurvedic): ayurvedic@test.com")
        print("-" * 60)
        print("\n🎯 To test:")
        print("1. Login as customer and browse categories")
        print("2. Login as vendor to test dashboard")
        print("3. Verify filtering and search work")
        print()

if __name__ == '__main__':
    create_sample_vendors()
