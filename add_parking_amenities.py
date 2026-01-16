from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN parking VARCHAR(20)"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN other_amenities TEXT"))
        conn.commit()
    print("Added parking and other_amenities columns")
