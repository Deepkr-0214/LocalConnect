from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN pure_veg BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN indoor_seating BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN outdoor_seating BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN home_delivery BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN takeaway BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN free_wifi BOOLEAN DEFAULT 0"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN opening_time VARCHAR(10)"))
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN closing_time VARCHAR(10)"))
        conn.commit()
    print("Added amenities and timing columns to vendor table")
