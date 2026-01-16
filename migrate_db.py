import sqlite3
import os

db_path = 'instance/database.db'

if not os.path.exists(db_path):
    print("Database not found. It will be created when you run the app.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if email column exists
        cursor.execute("PRAGMA table_info(vendor)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'email' not in columns:
            print("Migrating vendor table to add email column...")
            
            # Create new table with email
            cursor.execute("""
                CREATE TABLE vendor_new (
                    id INTEGER PRIMARY KEY,
                    business_name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    business_category VARCHAR(50) NOT NULL,
                    business_address VARCHAR(200) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    password_hash VARCHAR(128) NOT NULL
                )
            """)
            
            # Copy existing data (email will be set to business_name@temp.com)
            cursor.execute("""
                INSERT INTO vendor_new (id, business_name, email, business_category, business_address, phone, password_hash)
                SELECT id, business_name, business_name || '@temp.com', business_category, business_address, phone, password_hash
                FROM vendor
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE vendor")
            cursor.execute("ALTER TABLE vendor_new RENAME TO vendor")
            
            conn.commit()
            print("Migration complete!")
            print("NOTE: Existing vendors have temporary emails (business_name@temp.com)")
            print("They need to update their email or re-register.")
        else:
            print("Email column already exists")
        
        conn.close()
        print("\nYou can now restart the Flask app.")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nIf migration fails, delete instance/database.db and restart Flask.")
