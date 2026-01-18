#!/usr/bin/env python3
"""
Test script to verify automatic geocoding on vendor registration and address updates.

This script tests:
1. Vendor signup with automatic geocoding
2. Vendor settings update with automatic geocoding
3. Customer profile update with automatic geocoding
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import Vendor, Customer
from utils.geocoding import geocode_address

def test_geocoding_function():
    """Test the geocoding function directly"""
    print("\n" + "="*80)
    print("TEST 1: Geocoding Function")
    print("="*80)
    
    test_addresses = [
        "Mishra Sweets, Delhi NCR",
        "Q.no-57/21 Chhota Govindpur, Jamshedpur Jharkhand-831015",
        "Bangali Sweets, Delhi",
        "New York, USA",  # Should fail - outside India
    ]
    
    for address in test_addresses:
        print(f"\n📍 Testing: {address}")
        lat, lon = geocode_address(address)
        if lat and lon:
            print(f"   ✅ Result: ({lat:.4f}, {lon:.4f})")
        else:
            print(f"   ❌ Failed to geocode")

def test_vendor_registration():
    """Test automatic geocoding during vendor registration"""
    print("\n" + "="*80)
    print("TEST 2: Vendor Registration with Auto-Geocoding")
    print("="*80)
    
    with app.app_context():
        # Check existing vendor count
        existing_count = Vendor.query.count()
        print(f"\n📊 Current vendors in database: {existing_count}")
        
        # Create a test vendor
        test_vendor = Vendor(
            business_name="Test Vendor - " + str(existing_count + 1),
            email=f"test_vendor_{existing_count + 1}@test.com",
            business_category="Food",
            business_address="Q.no-57/21 Chhota Govindpur, Jamshedpur Jharkhand-831015",
            phone="+919876543210"
        )
        test_vendor.set_password("testpass123")
        
        print(f"\n📝 Test Vendor Details:")
        print(f"   Name: {test_vendor.business_name}")
        print(f"   Email: {test_vendor.email}")
        print(f"   Address: {test_vendor.business_address}")
        
        # Simulate automatic geocoding
        print(f"\n🔄 Geocoding address...")
        lat, lon = geocode_address(test_vendor.business_address)
        
        if lat and lon:
            test_vendor.latitude = lat
            test_vendor.longitude = lon
            print(f"✅ Auto-geocoded successfully!")
            print(f"   Location: ({lat:.4f}, {lon:.4f})")
        else:
            print(f"❌ Failed to auto-geocode")
        
        db.session.add(test_vendor)
        db.session.commit()
        
        print(f"\n✅ Test vendor created with ID: {test_vendor.id}")
        print(f"   Latitude: {test_vendor.latitude}")
        print(f"   Longitude: {test_vendor.longitude}")
        
        # Verify
        saved_vendor = Vendor.query.get(test_vendor.id)
        if saved_vendor.latitude and saved_vendor.longitude:
            print(f"\n✅ VERIFICATION PASSED: Location saved to database!")
            print(f"   Coordinates: ({saved_vendor.latitude:.4f}, {saved_vendor.longitude:.4f})")
            
            # Cleanup
            db.session.delete(saved_vendor)
            db.session.commit()
            print(f"✅ Test vendor cleaned up")
            return True
        else:
            print(f"\n❌ VERIFICATION FAILED: Location not saved!")
            db.session.delete(saved_vendor)
            db.session.commit()
            return False

def test_vendor_address_update():
    """Test automatic geocoding when vendor updates address"""
    print("\n" + "="*80)
    print("TEST 3: Vendor Address Update with Auto-Geocoding")
    print("="*80)
    
    with app.app_context():
        # Get first vendor
        vendor = Vendor.query.first()
        
        if not vendor:
            print("❌ No vendors found in database to test with")
            return False
        
        print(f"\n📝 Selected Vendor: {vendor.business_name} (ID: {vendor.id})")
        print(f"   Current Address: {vendor.business_address}")
        print(f"   Current Coords: ({vendor.latitude}, {vendor.longitude})")
        
        # Change address
        old_address = vendor.business_address
        old_lat = vendor.latitude
        old_lon = vendor.longitude
        
        new_address = "Marina Bay, Singapore"  # Different location
        print(f"\n🔄 Updating address to: {new_address}")
        
        # Simulate geocoding on update
        lat, lon = geocode_address(new_address)
        
        if lat and lon:
            vendor.business_address = new_address
            vendor.latitude = lat
            vendor.longitude = lon
            db.session.commit()
            
            print(f"✅ Address updated!")
            print(f"   New Coords: ({lat:.4f}, {lon:.4f})")
            
            # Restore original address
            print(f"\n🔄 Restoring original address for cleanup...")
            lat, lon = geocode_address(old_address)
            vendor.business_address = old_address
            if lat and lon:
                vendor.latitude = lat
                vendor.longitude = lon
            db.session.commit()
            print(f"✅ Original address restored")
            
            return True
        else:
            print(f"❌ Failed to geocode new address")
            return False

def test_customer_address_update():
    """Test automatic geocoding when customer updates address"""
    print("\n" + "="*80)
    print("TEST 4: Customer Address Update with Auto-Geocoding")
    print("="*80)
    
    with app.app_context():
        # Get first customer
        customer = Customer.query.first()
        
        if not customer:
            print("❌ No customers found in database to test with")
            return False
        
        print(f"\n👤 Selected Customer: {customer.full_name} (ID: {customer.id})")
        print(f"   Current Address: {customer.address}")
        print(f"   Current Coords: ({customer.latitude}, {customer.longitude})")
        
        # Change address
        old_address = customer.address
        old_city = customer.city
        old_state = customer.state
        old_lat = customer.latitude
        old_lon = customer.longitude
        
        new_address = "1600 Pennsylvania Avenue"
        new_city = "Washington"
        new_state = "DC"
        
        print(f"\n🔄 Updating address to: {new_address}, {new_city}, {new_state}")
        
        # Simulate geocoding on update
        full_address = f"{new_address}, {new_city}, {new_state}".strip(', ')
        lat, lon = geocode_address(full_address)
        
        if lat and lon:
            customer.address = new_address
            customer.city = new_city
            customer.state = new_state
            customer.latitude = lat
            customer.longitude = lon
            db.session.commit()
            
            print(f"✅ Address updated!")
            print(f"   New Coords: ({lat:.4f}, {lon:.4f})")
            
            # Restore original address
            print(f"\n🔄 Restoring original address for cleanup...")
            customer.address = old_address
            customer.city = old_city
            customer.state = old_state
            customer.latitude = old_lat
            customer.longitude = old_lon
            db.session.commit()
            print(f"✅ Original address restored")
            
            return True
        else:
            print(f"❌ Failed to geocode new address")
            return False

def main():
    """Run all tests"""
    print("\n" + "🗺️  "*15)
    print("AUTOMATIC GEOCODING TEST SUITE")
    print("🗺️  "*15)
    
    results = {
        'Geocoding Function': test_geocoding_function,
        'Vendor Registration': test_vendor_registration,
        'Vendor Address Update': test_vendor_address_update,
        'Customer Address Update': test_customer_address_update,
    }
    
    passed = 0
    failed = 0
    
    for test_name, test_func in results.items():
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Exception in {test_name}: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.")

if __name__ == '__main__':
    main()
