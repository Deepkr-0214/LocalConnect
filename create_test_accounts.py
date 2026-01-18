"""
Create test accounts for debugging
"""
from app import app, db, Customer, Vendor
from werkzeug.security import generate_password_hash

def create_test_accounts():
    with app.app_context():
        # Create test customer
        test_customer = Customer.query.filter_by(email='test@customer.com').first()
        if not test_customer:
            test_customer = Customer(
                full_name='Test Customer',
                email='test@customer.com',
                phone='+919876543210'
            )
            test_customer.set_password('test123')
            db.session.add(test_customer)
            print("Created test customer: test@customer.com / test123")
        
        # Create test vendor
        test_vendor = Vendor.query.filter_by(email='test@vendor.com').first()
        if not test_vendor:
            test_vendor = Vendor(
                business_name='Test Restaurant',
                email='test@vendor.com',
                business_category='Restaurant',
                business_address='Test Address, Test City',
                phone='+919876543211'
            )
            test_vendor.set_password('test123')
            db.session.add(test_vendor)
            print("Created test vendor: test@vendor.com / test123")
        
        db.session.commit()
        print("Test accounts created successfully!")
        print("\nLogin credentials:")
        print("Customer: test@customer.com / test123")
        print("Vendor: test@vendor.com / test123")

if __name__ == '__main__':
    create_test_accounts()