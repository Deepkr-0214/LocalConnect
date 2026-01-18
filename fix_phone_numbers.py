#!/usr/bin/env python3
"""
Fix phone numbers in database by adding +91 country code
"""

from models.models import db, Vendor, Customer
from app import app

def fix_phone_numbers():
    print("🔧 Fixing phone numbers in database...")
    print("=" * 50)

    with app.app_context():
        # Fix vendor phone numbers
        vendors = Vendor.query.all()
        print(f"📊 Processing {len(vendors)} vendors...")

        for vendor in vendors:
            if vendor.phone and not vendor.phone.startswith('+'):
                old_phone = vendor.phone
                # Remove any leading zeros and add +91
                clean_phone = vendor.phone.lstrip('0')
                new_phone = f"+91{clean_phone}"
                vendor.phone = new_phone
                print(f"✅ Vendor {vendor.business_name}: {old_phone} → {new_phone}")

        # Fix customer phone numbers
        customers = Customer.query.all()
        print(f"\n📊 Processing {len(customers)} customers...")

        for customer in customers:
            if customer.phone and not customer.phone.startswith('+'):
                old_phone = customer.phone
                # Remove any leading zeros and add +91
                clean_phone = customer.phone.lstrip('0')
                new_phone = f"+91{clean_phone}"
                customer.phone = new_phone
                print(f"✅ Customer {customer.full_name}: {old_phone} → {new_phone}")

        # Commit changes
        db.session.commit()
        print("\n✅ All phone numbers updated successfully!")

        # Verify changes
        print("\n🔍 Verification:")
        vendors = Vendor.query.all()
        for vendor in vendors:
            print(f"🏪 {vendor.business_name}: {vendor.phone}")

if __name__ == "__main__":
    fix_phone_numbers()
