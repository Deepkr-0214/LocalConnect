"""
Create test vendor accounts for all categories to verify implementation
"""
from app import app, db
from models.models import Vendor

def create_test_vendors():
    """Create test vendor accounts for each category"""
    
    test_vendors = [
        {
            'business_name': 'Test Garage Services',
            'email': 'garage@test.com',
            'business_category': 'Garage',
            'business_sub_category': '2-Wheeler',
            'business_address': 'Test Address, Delhi',
            'phone': '+919876543210',
            'password': 'test123',
            'latitude': 28.6139,
            'longitude': 77.2090
        },
        {
            'business_name': 'Test Electronics Store',
            'email': 'electronics@test.com',
            'business_category': 'Electronics',
            'business_sub_category': 'Mobiles',
            'business_address': 'Test Address, Delhi',
            'phone': '+919876543211',
            'password': 'test123',
            'latitude': 28.6139,
            'longitude': 77.2090
        },
        {
            'business_name': 'Test Fashion Boutique',
            'email': 'fashion@test.com',
            'business_category': 'Fashion',
            'business_sub_category': 'Ladies',
            'business_address': 'Test Address, Delhi',
            'phone': '+919876543212',
            'password': 'test123',
            'latitude': 28.6139,
            'longitude': 77.2090
        },
        {
            'business_name': 'Test Grocery Store',
            'email': 'grocery@test.com',
            'business_category': 'Grocery',
            'business_sub_category': 'Vegetables',
            'business_address': 'Test Address, Delhi',
            'phone': '+919876543213',
            'password': 'test123',
            'latitude': 28.6139,
            'longitude': 77.2090
        },
        {
            'business_name': 'Test Pharmacy',
            'email': 'pharmacy@test.com',
            'business_category': 'Pharmacy',
            'business_sub_category': 'Chemist & Drug Medicine',
            'business_address': 'Test Address, Delhi',
            'phone': '+919876543214',
            'password': 'test123',
            'latitude': 28.6139,
            'longitude': 77.2090
        }
    ]
    
    with app.app_context():
        created_count = 0
        for vendor_data in test_vendors:
            # Check if vendor already exists
            existing = Vendor.query.filter_by(email=vendor_data['email']).first()
            if existing:
                print(f"✓ Vendor already exists: {vendor_data['business_name']} ({vendor_data['business_category']})")
                continue
            
            # Create new vendor
            vendor = Vendor(
                business_name=vendor_data['business_name'],
                email=vendor_data['email'],
                business_category=vendor_data['business_category'],
                business_sub_category=vendor_data['business_sub_category'],
                business_address=vendor_data['business_address'],
                phone=vendor_data['phone'],
                latitude=vendor_data['latitude'],
                longitude=vendor_data['longitude']
            )
            vendor.set_password(vendor_data['password'])
            
            db.session.add(vendor)
            created_count += 1
            print(f"✓ Created: {vendor_data['business_name']} ({vendor_data['business_category']})")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n✅ Successfully created {created_count} test vendor(s)")
        else:
            print(f"\n✅ All test vendors already exist")
        
        print("\n" + "="*60)
        print("TEST VENDOR CREDENTIALS")
        print("="*60)
        for vendor_data in test_vendors:
            print(f"\n{vendor_data['business_category']} Vendor:")
            print(f"  Email: {vendor_data['email']}")
            print(f"  Password: {vendor_data['password']}")
            print(f"  Category: {vendor_data['business_category']}")
        print("="*60)

if __name__ == '__main__':
    create_test_vendors()
