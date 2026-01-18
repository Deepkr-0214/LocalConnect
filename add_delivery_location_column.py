#!/usr/bin/env python3
"""
Add delivery location columns to Order table
"""

import sqlite3
import os

def add_location_columns():
    """Add location coordinate columns to the order table"""
    
    # Database path
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the app first to create the database.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info('order')")
        columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = [
            ('delivery_location_type', 'VARCHAR(20)'),
            ('vendor_latitude', 'FLOAT'),
            ('vendor_longitude', 'FLOAT'),
            ('customer_delivery_latitude', 'FLOAT'),
            ('customer_delivery_longitude', 'FLOAT')
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                cursor.execute(f'ALTER TABLE "order" ADD COLUMN {column_name} {column_type}')
                print(f"✅ Added column '{column_name}' to order table")
            else:
                print(f"✅ Column '{column_name}' already exists")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")

if __name__ == '__main__':
    print("🔧 Adding location columns to Order table...")
    add_location_columns()
    print("✅ Migration complete!")