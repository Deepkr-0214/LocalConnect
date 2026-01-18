import sqlite3

# Connect to database
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

try:
    # Add vendor response columns to Order table
    cursor.execute('ALTER TABLE "order" ADD COLUMN vendor_response TEXT')
    cursor.execute('ALTER TABLE "order" ADD COLUMN vendor_response_date DATETIME')
    cursor.execute('ALTER TABLE "order" ADD COLUMN response_helpful INTEGER DEFAULT 0')
    
    conn.commit()
    print("Vendor response columns added successfully!")
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Columns already exist")
    else:
        print(f"Error: {e}")

conn.close()