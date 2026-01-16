import sqlite3

# Connect to database
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(vendor)")
columns = [col[1] for col in cursor.fetchall()]

if 'is_open' not in columns:
    print("Adding is_open column to vendor table...")
    cursor.execute("ALTER TABLE vendor ADD COLUMN is_open BOOLEAN DEFAULT 1")
    conn.commit()
    print("Column added successfully!")
else:
    print("Column is_open already exists.")

conn.close()
