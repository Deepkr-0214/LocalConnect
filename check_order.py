import sqlite3

conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info('order')")
columns = cursor.fetchall()

print("Current order table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
