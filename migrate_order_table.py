import sqlite3
import os

db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print("Database not found. It will be created when you run the app.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current columns in order table
        cursor.execute("PRAGMA table_info(\"order\")")
        columns = [col[1] for col in cursor.fetchall()]

        print("Current order table columns:", columns)

        # Add missing columns one by one
        missing_columns = {
            'vendor_id': 'INTEGER',
            'customer_name': 'VARCHAR(100)',
            'customer_phone': 'VARCHAR(20)',
            'items_summary': 'VARCHAR(500)',
            'order_type': 'VARCHAR(20)',
            'customer_suggestion': 'TEXT',
            'rejection_reason': 'TEXT'
        }

        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                print(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE \"order\" ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")

        # Update existing orders with vendor_id based on vendor_name
        # First, get vendor mapping
        cursor.execute("SELECT id, business_name FROM vendor")
        vendors = cursor.fetchall()
        vendor_map = {name: id for id, name in vendors}

        cursor.execute("SELECT id, vendor_name FROM \"order\" WHERE vendor_id IS NULL")
        orders_to_update = cursor.fetchall()

        for order_id, vendor_name in orders_to_update:
            if vendor_name in vendor_map:
                cursor.execute("UPDATE \"order\" SET vendor_id = ? WHERE id = ?", (vendor_map[vendor_name], order_id))
                print(f"Updated order {order_id} with vendor_id {vendor_map[vendor_name]}")
            else:
                print(f"Warning: Could not find vendor '{vendor_name}' for order {order_id}")

        conn.commit()
        print("Migration complete!")

        conn.close()
        print("\nYou can now restart the Flask app.")

    except Exception as e:
        print(f"Error: {e}")
        print("\nIf migration fails, delete instance/database.db and restart Flask.")
