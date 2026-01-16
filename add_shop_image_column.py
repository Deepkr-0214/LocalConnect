from app import app, db
from models.models import Vendor

with app.app_context():
    # Add shop_image column
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE vendor ADD COLUMN shop_image VARCHAR(200) DEFAULT '🏪'"))
        conn.commit()
    print("Added shop_image column to vendor table")
