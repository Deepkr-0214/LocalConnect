#!/usr/bin/env python3
"""Quick check for Chicken Street Food vendor"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import Vendor
from geocoding_enhanced import GeocodeServiceEnhanced

def main():
    print("\n" + "="*80)
    print("🔍 CHECKING CHICKEN STREET FOOD VENDOR")
    print("="*80)
    
    with app.app_context():
        # Search for vendor
        vendor = Vendor.query.filter(
            Vendor.business_name.ilike('%chicken%street%')
        ).first()
        
        if not vendor:
            print("\n❌ Vendor not found with 'Chicken Street Food' name")
            print("\nSearching all vendors with 'Chicken' in name...")
            vendors = Vendor.query.filter(
                Vendor.business_name.ilike('%chicken%')
            ).all()
            
            if vendors:
                print(f"\nFound {len(vendors)} vendor(s) with 'Chicken':")
                for v in vendors:
                    print(f"\n  ID: {v.id}")
                    print(f"  Name: {v.business_name}")
                    print(f"  Address: {v.business_address}")
                    print(f"  Coordinates: Lat={v.latitude}, Lon={v.longitude}")
                    
                    if not v.latitude or not v.longitude:
                        print(f"  ⚠️  MISSING COORDINATES - Attempting to geocode...")
                        service = GeocodeServiceEnhanced()
                        lat, lon = service.geocode(v.business_address)
                        
                        if lat and lon:
                            print(f"  ✅ Geocoded to: ({lat:.4f}, {lon:.4f})")
                            print(f"  Saving to database...")
                            v.latitude = lat
                            v.longitude = lon
                            db.session.commit()
                            print(f"  ✅ SAVED!")
                        else:
                            print(f"  ❌ Could not geocode - address may be incomplete")
                            print(f"  Try adding city and state to address")
            else:
                print("\n❌ No vendors with 'Chicken' found")
                print("\nAll vendors in database:")
                all_vendors = Vendor.query.all()
                for v in all_vendors[:15]:
                    status = "✅ HAS COORDS" if v.latitude and v.longitude else "❌ NO COORDS"
                    print(f"  {v.id}: {v.business_name} - {status}")
        else:
            print("\n✅ FOUND: Chicken Street Food")
            print(f"\nID: {vendor.id}")
            print(f"Name: {vendor.business_name}")
            print(f"Address: {vendor.business_address}")
            print(f"Current Coordinates: Lat={vendor.latitude}, Lon={vendor.longitude}")
            
            if vendor.latitude and vendor.longitude:
                print(f"\n✅ COORDINATES EXIST")
                print(f"   Location: ({vendor.latitude:.4f}, {vendor.longitude:.4f})")
            else:
                print(f"\n❌ MISSING COORDINATES")
                print(f"   Attempting to geocode address...")
                
                service = GeocodeServiceEnhanced()
                lat, lon = service.geocode(vendor.business_address)
                
                if lat and lon:
                    print(f"\n✅ Geocoding successful: ({lat:.4f}, {lon:.4f})")
                    print(f"   Saving to database...")
                    vendor.latitude = lat
                    vendor.longitude = lon
                    db.session.commit()
                    print(f"   ✅ SAVED! Vendor will now appear on map")
                else:
                    print(f"\n❌ Geocoding failed")
                    print(f"   Possible reasons:")
                    print(f"   1. Address incomplete (missing city/state)")
                    print(f"   2. Address has typos")
                    print(f"   3. Location doesn't exist in Nominatim database")
                    print(f"\n   Current address: '{vendor.business_address}'")
                    print(f"   Better format: 'Business Name, City, State'")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
