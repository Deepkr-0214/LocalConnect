#!/usr/bin/env python
"""
Direct fix for vendor coordinates using manual updates based on known addresses.
"""

import sqlite3
import os

def fix_vendor_coordinates_manual():
    """Directly fix known incorrect vendor coordinates."""
    
    db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("VENDOR COORDINATE FIX - MANUAL UPDATE")
    print("=" * 130)
    print()
    
    # Define correct coordinates for known addresses
    corrections = {
        5: {  # Jamshedpur vendor
            'name': 'NA',
            'address': 'Q.no-57/21 Chhota Govindpur , Jamshedpur Jharkhand-831015',
            'new_lat': 22.8015194,  # Jamshedpur, Jharkhand
            'new_lon': 86.2029579,
            'reason': 'Address is in Jamshedpur, Jharkhand (not Delhi NCR)'
        },
        7: {  # Jamshedpur vendor
            'name': 'Briyani House',
            'address': 'Q.no:-57/2/1 CHHOTA GOVINDPUR JAMSHEDPUR JHARKHAND-831015',
            'new_lat': 22.8015194,  # Jamshedpur, Jharkhand
            'new_lon': 86.2029579,
            'reason': 'Address is in Jamshedpur, Jharkhand (not Delhi NCR)'
        }
    }
    
    fixed_count = 0
    
    for vendor_id, correction in corrections.items():
        cursor.execute('SELECT latitude, longitude FROM vendor WHERE id = ?', (vendor_id,))
        result = cursor.fetchone()
        
        if result:
            old_lat, old_lon = result
            new_lat = correction['new_lat']
            new_lon = correction['new_lon']
            
            print(f"Vendor ID {vendor_id}: {correction['name']}")
            print(f"  Address: {correction['address']}")
            print(f"  Reason: {correction['reason']}")
            print(f"  Old Coordinates: Lat={old_lat}, Lon={old_lon}")
            print(f"  New Coordinates: Lat={new_lat}, Lon={new_lon}")
            
            # Update database
            cursor.execute(
                'UPDATE vendor SET latitude = ?, longitude = ? WHERE id = ?',
                (new_lat, new_lon, vendor_id)
            )
            fixed_count += 1
            print(f"  ✓ Updated successfully\n")
    
    conn.commit()
    
    print("=" * 130)
    print(f"Fixed {fixed_count} vendor coordinates\n")
    
    print("VERIFICATION - Current Vendor Locations:")
    print("-" * 130)
    
    cursor.execute('SELECT id, business_name, business_address, latitude, longitude FROM vendor')
    vendors = cursor.fetchall()
    
    for vendor_id, name, address, lat, lon in vendors:
        print(f"ID {vendor_id}: {name}")
        print(f"  Address: {address}")
        print(f"  Coordinates: Lat={lat:.6f}, Lon={lon:.6f}")
        
        # Determine location region
        if 28.5 < lat < 28.8 and 77.0 < lon < 77.4:
            region = "📍 Delhi NCR Region"
        elif 22.7 < lat < 22.9 and 86.1 < lon < 86.3:
            region = "📍 Jamshedpur, Jharkhand"
        elif 25.5 < lat < 25.7 and 85.1 < lon < 85.3:
            region = "📍 Patna, Bihar"
        else:
            region = "📍 Other Region"
        
        print(f"  {region}\n")
    
    conn.close()
    print("Done! Vendor coordinates have been corrected.")

if __name__ == '__main__':
    fix_vendor_coordinates_manual()
