from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("ALTER TABLE vendor RENAME COLUMN food_type TO category_type"))
        except:
            conn.execute(db.text("ALTER TABLE vendor ADD COLUMN category_type VARCHAR(50)"))
        conn.commit()
    print("Renamed food_type to category_type")
