import sqlite3
import os

db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print("Database not found.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if vendor_id column exists in order table
        cursor.execute("PRAGMA table_info('order')")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'vendor_id' not in columns:
            print("Migrating order table to add vendor_id column...")
            
            # Create new table with vendor_id
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
            
            # Copy existing data (set vendor_id to 1 for old orders)
            cursor.execute("""
                INSERT INTO order_new (id, customer_id, vendor_id, vendor_name, customer_name, customer_phone,
                                      items, items_summary, delivery_type, payment_type, total, status,
                                      order_type, customer_suggestion, rejection_reason, created_at,
                                      review_rating, review_comment, review_date)
                SELECT id, customer_id, 1, vendor_name, customer_name, customer_phone,
                       items, items_summary, delivery_type, payment_type, total, status,
                       order_type, customer_suggestion, rejection_reason, created_at,
                       review_rating, review_comment, review_date
                FROM "order"
            """)
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE "order"')
            cursor.execute('ALTER TABLE order_new RENAME TO "order"')
            
            conn.commit()
            print("Migration complete!")
            print("NOTE: Existing orders assigned to vendor_id=1")
        else:
            print("vendor_id column already exists in order table")
        
        conn.close()
        print("\nYou can now restart the Flask app.")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nIf migration fails, delete instance/database.db and restart Flask.")
