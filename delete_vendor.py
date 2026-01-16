from app import app, db
from models.models import Vendor, MenuItem, Order

with app.app_context():
    vendor = Vendor.query.filter_by(email='deepkumarsinha2005@gmail.com').first()
    if vendor:
        # Delete related menu items
        MenuItem.query.filter_by(vendor_id=vendor.id).delete()
        # Delete related orders
        Order.query.filter_by(vendor_id=vendor.id).delete()
        # Delete vendor
        db.session.delete(vendor)
        db.session.commit()
        print(f"Deleted vendor: {vendor.business_name}")
    else:
        print("Vendor not found")
