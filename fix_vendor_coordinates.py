#!/usr/bin/env python
"""
Fix incorrect vendor coordinates in the database.
This script identifies vendors with addresses in different states and re-geocodes them correctly.
"""

import sqlite3
import os
from utils.geocoding import geocode_address

def fix_vendor_coordinates():
    """Fix incorrect coordinates for vendors with addresses from different states."""
    
    db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("VENDOR COORDINATE FIX UTILITY")
    print("=" * 120)
    print()
    
    # Get all vendors
    cursor.execute('SELECT id, business_name, business_address, latitude, longitude FROM vendor')
    vendors = cursor.fetchall()
    
    print(f"Found {len(vendors)} vendors in database\n")
    
    fixed_count = 0
    
    for vendor_id, name, address, lat, lon in vendors:
        if not address:
            continue
            
        # Geocode the address
        print(f"Processing Vendor ID {vendor_id}: {name}")
        print(f"  Address: {address}")
        
        new_lat, new_lon = geocode_address(address)
        
        if new_lat is None or new_lon is None:
            print(f"  ✗ Could not geocode address")
        else:
            print(f"  New coordinates: Lat={new_lat:.6f}, Lon={new_lon:.6f}")
            
            if lat is not None and lon is not None:
                # Check if coordinates changed significantly
                lat_diff = abs(float(lat) - new_lat)
                lon_diff = abs(float(lon) - new_lon)
                
                if lat_diff > 0.1 or lon_diff > 0.1:  # More than ~10km difference
                    print(f"  ⚠️  CORRECTING: Old Lat={lat:.6f}, Lon={lon:.6f}")
                    print(f"              → New Lat={new_lat:.6f}, Lon={new_lon:.6f}")
                    cursor.execute(
                        'UPDATE vendor SET latitude = ?, longitude = ? WHERE id = ?',
                        (new_lat, new_lon, vendor_id)
                    )
                    fixed_count += 1
                    print(f"  ✓ Updated successfully")
                else:
                    print(f"  ✓ Coordinates are already correct")
            else:
                # No previous coordinates
                print(f"  ✓ Setting new coordinates")
                cursor.execute(
                    'UPDATE vendor SET latitude = ?, longitude = ? WHERE id = ?',
                    (new_lat, new_lon, vendor_id)
                )
                fixed_count += 1
        
        print()
    
    # Commit changes
    conn.commit()
    
    print("=" * 120)
    print(f"Fixed {fixed_count} vendor coordinates")
    print("\nVerifying fixed vendors:")
    print("-" * 120)
    
    cursor.execute('SELECT id, business_name, business_address, latitude, longitude FROM vendor')
    vendors = cursor.fetchall()
    
    for vendor_id, name, address, lat, lon in vendors:
        print(f"ID {vendor_id}: {name}")
        print(f"  Address: {address}")
        print(f"  Coordinates: Lat={lat}, Lon={lon}")
        print()
    
    conn.close()
    print("Done!")

if __name__ == '__main__':
    fix_vendor_coordinates()
