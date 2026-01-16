import sqlite3
import os

db_path = 'instance/database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check order table structure
    cursor.execute("PRAGMA table_info(\"order\")")
    columns = cursor.fetchall()
    print("Order table columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")

    # Check if there are any orders
    cursor.execute("SELECT COUNT(*) FROM \"order\"")
    count = cursor.fetchone()[0]
    print(f"\nTotal orders: {count}")

    if count > 0:
        cursor.execute("SELECT id, customer_id, vendor_name FROM \"order\" LIMIT 5")
        orders = cursor.fetchall()
        print("\nSample orders:")
        for order in orders:
            print(f"  ID: {order[0]}, Customer ID: {order[1]}, Vendor Name: {order[2]}")

    conn.close()
else:
    print("Database not found.")
