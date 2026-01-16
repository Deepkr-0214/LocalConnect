import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("razorpay_order_id", "TEXT"),
        ("razorpay_payment_id", "TEXT"),
        ("razorpay_signature", "TEXT")
    ]

    for column_name, column_type in columns_to_add:
        try:
            print(f"Adding column {column_name}...")
            cursor.execute(f"ALTER TABLE `order` ADD COLUMN {column_name} {column_type}")
            print(f"Successfully added {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {column_name} already exists")
            else:
                print(f"Error adding {column_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
