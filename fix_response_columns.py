import sqlite3

# Connect to database
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

try:
    # Check existing columns first
    cursor.execute("PRAGMA table_info('order')")
    columns = [column[1] for column in cursor.fetchall()]
    print("Existing columns:", columns)
    
    # Add vendor response columns if they don't exist
    if 'vendor_response' not in columns:
        cursor.execute('ALTER TABLE "order" ADD COLUMN vendor_response TEXT')
        print("Added vendor_response column")
    
    if 'vendor_response_date' not in columns:
        cursor.execute('ALTER TABLE "order" ADD COLUMN vendor_response_date DATETIME')
        print("Added vendor_response_date column")
    
    if 'response_helpful' not in columns:
        cursor.execute('ALTER TABLE "order" ADD COLUMN response_helpful INTEGER DEFAULT 0')
        print("Added response_helpful column")
    
    conn.commit()
    print("Database updated successfully!")
    
except Exception as e:
    print(f"Error: {e}")

conn.close()