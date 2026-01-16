import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.getcwd(), 'instance', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add total_price column to order table
    cursor.execute('ALTER TABLE "order" ADD COLUMN total_price FLOAT')
    
    # Copy values from total to total_price for existing records
    cursor.execute('UPDATE "order" SET total_price = total WHERE total_price IS NULL')
    
    conn.commit()
    print("Successfully added total_price column to order table")
    print("Copied existing total values to total_price")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column total_price already exists")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
