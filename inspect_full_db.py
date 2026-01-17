import sqlite3
import os

db_path = 'instance/database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open('db_schema.txt', 'w', encoding='utf-8') as f:
        f.write(f"Found {len(tables)} tables.\n")

        for table_name in tables:
            table = table_name[0]
            if table.startswith('sqlite_'): continue
            
            f.write(f"\nTable: {table}\n")
            cursor.execute(f"PRAGMA table_info(\"{table}\")")
            columns = cursor.fetchall()
            for col in columns:
                # col[1] is name, col[2] is type
                f.write(f"  {col[1]} ({col[2]})\n")

    conn.close()
    print("Schema written to db_schema.txt")
else:
    print("Database not found.")
