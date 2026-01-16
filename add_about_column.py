from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN about TEXT"))
        conn.commit()
    print("Added 'about' column to vendor table")
