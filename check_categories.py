from app import app, db
from models.models import Vendor

with app.app_context():
    categories = db.session.query(Vendor.business_category).distinct().all()
    print("Existing categories:")
    for cat in categories:
        print(f"  - {cat[0]}")
