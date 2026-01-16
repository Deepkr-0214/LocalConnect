import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add columns to customer table
    customer_columns = [
        ("latitude", "REAL"),
        ("longitude", "REAL")
    ]

    for column_name, column_type in customer_columns:
        try:
            print(f"Adding column {column_name} to customer table...")
            cursor.execute(f"ALTER TABLE customer ADD COLUMN {column_name} {column_type}")
            print(f"Successfully added {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {column_name} already exists in customer table")
            else:
                print(f"Error adding {column_name} to customer: {e}")

    # Add columns to vendor table
    vendor_columns = [
        ("latitude", "REAL"),
        ("longitude", "REAL")
    ]

    for column_name, column_type in vendor_columns:
        try:
            print(f"Adding column {column_name} to vendor table...")
            cursor.execute(f"ALTER TABLE vendor ADD COLUMN {column_name} {column_type}")
            print(f"Successfully added {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {column_name} already exists in vendor table")
            else:
                print(f"Error adding {column_name} to vendor: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
