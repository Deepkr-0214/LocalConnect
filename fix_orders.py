import sqlite3
import os

db_path = 'instance/database.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop order_new if it exists
cursor.execute('DROP TABLE IF EXISTS order_new')
print("Cleaned up order_new table")

# Check if vendor_id exists
cursor.execute("PRAGMA table_info('order')")
columns = [col[1] for col in cursor.fetchall()]

if 'vendor_id' not in columns:
    print("Adding vendor_id and missing columns to order table...")
    
    # Create new table with all columns
    cursor.execute("""
        CREATE TABLE order_new (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            vendor_name VARCHAR(100) NOT NULL,
            customer_name VARCHAR(100),
            customer_phone VARCHAR(20),
            items TEXT NOT NULL,
            items_summary VARCHAR(500),
            delivery_type VARCHAR(20) NOT NULL,
            payment_type VARCHAR(20) NOT NULL,
            total FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'Pending',
            order_type VARCHAR(20),
            customer_suggestion TEXT,
            rejection_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            review_rating INTEGER,
            review_comment TEXT,
            review_date DATETIME,
            FOREIGN KEY (customer_id) REFERENCES customer(id),
            FOREIGN KEY (vendor_id) REFERENCES vendor(id)
        )
    """)
    
    # Copy existing data with defaults for new columns
    cursor.execute("""
        INSERT INTO order_new (id, customer_id, vendor_id, vendor_name, customer_name, customer_phone,
                              items, items_summary, delivery_type, payment_type, total, status,
                              order_type, customer_suggestion, rejection_reason, created_at,
                              review_rating, review_comment, review_date)
        SELECT id, customer_id, 1, vendor_name, NULL, NULL,
               items, NULL, delivery_type, payment_type, total, status,
               delivery_type, NULL, NULL, created_at,
               review_rating, review_comment, review_date
        FROM "order"
    """)
    
    # Replace table
    cursor.execute('DROP TABLE "order"')
    cursor.execute('ALTER TABLE order_new RENAME TO "order"')
    
    conn.commit()
    print("Migration complete! All orders assigned to vendor_id=1")
else:
    print("vendor_id already exists")

conn.close()
print("Done! Restart Flask.")
