#!/usr/bin/env python3
"""
Test script to verify location coordinates are stored in orders
"""

import sqlite3
import os

def test_location_storage():
    """Test if location coordinates are being stored in orders"""
    
    print("🧪 Testing Location Coordinate Storage")
    print("=" * 50)
    
    # Database path
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the app first.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if new columns exist
        cursor.execute("PRAGMA table_info('order')")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'delivery_location_type',
            'vendor_latitude', 
            'vendor_longitude',
            'customer_delivery_latitude',
            'customer_delivery_longitude'
        ]
        
        print("📋 Checking database schema:")
        for col in required_columns:
            if col in columns:
                print(f"  ✅ {col} - EXISTS")
            else:
                print(f"  ❌ {col} - MISSING")
        
        # Check if there are any orders with location data
        cursor.execute("""
            SELECT id, vendor_latitude, vendor_longitude, 
                   customer_delivery_latitude, customer_delivery_longitude,
                   delivery_location_type
            FROM 'order' 
            WHERE vendor_latitude IS NOT NULL 
            LIMIT 5
        """)
        
        orders = cursor.fetchall()
        
        print(f"\n📊 Found {len(orders)} orders with location data:")
        for order in orders:
            order_id, v_lat, v_lon, c_lat, c_lon, loc_type = order
            print(f"  Order #{order_id}:")
            print(f"    Vendor: ({v_lat}, {v_lon})")
            print(f"    Customer: ({c_lat}, {c_lon})")
            print(f"    Location Type: {loc_type}")
        
        conn.close()
        
        print("\n✅ Location coordinate storage test complete!")
        
    except Exception as e:
        print(f"❌ Error testing location storage: {e}")

if __name__ == '__main__':
    test_location_storage()