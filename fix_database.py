import sqlite3
import os
from flask import Flask
from models.models import db, Customer, Vendor, Order, MenuItem

# Configuration
DB_PATH = 'instance/database.db'
TEMP_DB_PATH = 'instance/temp_database.db'

def fix_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), DB_PATH)}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    # 1. Rename existing tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['customer', 'vendor', 'menu_item', 'order'] # 'review' is dropped
    
    try:
        # Check if tables exist before renaming
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [r[0] for r in cursor.fetchall()]
        
        for table in tables:
            if table in existing_tables:
                print(f"Renaming {table} to {table}_old")
                cursor.execute(f"ALTER TABLE \"{table}\" RENAME TO \"{table}_old\"")
        
        # Drop review table if exists
        if 'review' in existing_tables:
             print("Dropping review table (not in models)")
             cursor.execute("DROP TABLE IF EXISTS review")

        conn.commit()
        conn.close()
        
        # 2. Create new tables
        print("Creating new tables from models...")
        with app.app_context():
            db.create_all()
            
        # 3. Copy data
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Migrating data...")
        
        # Helper to copy data
        def copy_table(table_name, columns):
            # columns is list of column names in new table
            print(f"Migrating {table_name}...")
            # Get columns from old table
            cursor.execute(f"PRAGMA table_info(\"{table_name}_old\")")
            old_cols_info = cursor.fetchall()
            old_cols = [c['name'] for c in old_cols_info]
            
            # Intersection of columns
            common_cols = [c for c in columns if c in old_cols]
            
            if not common_cols:
                print(f"No common columns for {table_name}, skipping data.")
                return

            cols_str = ", ".join(common_cols)
            sql = f"INSERT INTO \"{table_name}\" ({cols_str}) SELECT {cols_str} FROM \"{table_name}_old\""
            cursor.execute(sql)
            print(f"Copied {cursor.rowcount} rows for {table_name}.")

        # Get column names for each model
        with app.app_context():
            copy_table('customer', Customer.__table__.columns.keys())
            copy_table('vendor', Vendor.__table__.columns.keys())
            copy_table('menu_item', MenuItem.__table__.columns.keys())
            copy_table('order', Order.__table__.columns.keys())

        # 4. Cleanup
        print("Cleaning up old tables...")
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS \"{table}_old\"")
            
        conn.commit()
        conn.close()
        print("Database fixed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    fix_database()
