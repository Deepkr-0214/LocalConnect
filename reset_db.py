import os
import time

db_path = 'instance/database.db'

# Try to delete the database
try:
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Deleted {db_path}")
    else:
        print(f"Database file not found at {db_path}")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nPlease:")
    print("1. Stop Flask server (Ctrl+C)")
    print("2. Manually delete: instance\\database.db")
    print("3. Restart Flask: python app.py")
