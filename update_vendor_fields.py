from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        # Drop pure_veg column and add food_type
        try:
            conn.execute(db.text("ALTER TABLE vendor DROP COLUMN pure_veg"))
        except:
            pass
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN food_type VARCHAR(20)"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN ac BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN cooler BOOLEAN DEFAULT 0"))
        conn.commit()
    print("Updated vendor table with food_type, AC, and cooler columns")
