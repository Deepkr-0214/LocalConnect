from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN veg_nonveg VARCHAR(20)"))
        conn.commit()
    print("Added veg_nonveg column")
