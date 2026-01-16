# init_db.py
from app import app, db
from models import MenuItem, Order, Vendor, Review
from datetime import datetime

with app.app_context():
    # 1. Clear existing data (Optional - start fresh)
    db.drop_all()
    db.create_all()

    # 2. Add a Vendor Profile
    vendor = Vendor(
        shop_name="Localconnect Shop",
        email="vendor@localconnect.com",
        is_open=True
    )

    # 3. Add Menu Items (Matching your menu.jpg)
    items = [
        MenuItem(name="Paneer Tikka", sub_name="Rahul Sharma", category="Veg", price=180.0),
        MenuItem(name="Chicken Biryani", sub_name="Butter Naan", category="Non-Veg", price=250.0),
        MenuItem(name="Masala Dosa", sub_name="Garlic Naan", category="Veg", price=150.0),
        MenuItem(name="Veg Burger", sub_name="Butter Naan", category="Veg", price=100.0)
    ]

    # 4. Add Orders (Matching your dashboard.jpg and orders.jpg)
    orders = [
        Order(id=1023, customer_name="Amit Patel", items_summary="Chicken Biryani, Butter Naan", total_price=450.0, status="Pending", order_type="Takeaway", customer_suggestion="Please make it extra spicy"),
        Order(id=1022, customer_name="Priya Verma", items_summary="Paneer Tikka, Garlic Naan", total_price=320.0, status="Completed", order_type="Delivery", customer_suggestion="Less oil please"),
        Order(id=1021, customer_name="Rahul Sharma", items_summary="Veg Burger, Fries", total_price=200.0, status="Rejected", order_type="Takeaway"),
        Order(id=1020, customer_name="Sneha Reddy", items_summary="Masala Dosa, Sambar", total_price=180.0, status="Pending", order_type="Delivery", customer_suggestion="Extra chutney please"),
        Order(id=1019, customer_name="Vikram Singh", items_summary="Chicken Tikka, Roti", total_price=280.0, status="Completed", order_type="Takeaway")
    ]

    # 5. Add Reviews with diverse ratings and responses
    reviews = [
        # 5-star reviews
        Review(customer_name="Amit Patel", rating=5.0, comment="Excellent taste! The food was amazing and delivery was quick. Best restaurant in the area!"),
        Review(customer_name="Anita Gupta", rating=5.0, comment="Outstanding service and delicious food! Will definitely order again.", response="Thank you so much for your wonderful review!", response_date=datetime.now(), is_helpful=True),
        Review(customer_name="Rajesh Kumar", rating=5.0, comment="Perfect! Everything was fresh and tasty. Highly recommended!"),
        
        # 4-star reviews
        Review(customer_name="Sneha Reddy", rating=4.0, comment="Good food but delivery was a bit slow. Overall satisfied with the quality.", response="Thank you for your feedback! We're working on improving our delivery times.", response_date=datetime.now()),
        Review(customer_name="Vikram Sharma", rating=4.0, comment="Nice taste and good packaging. Could improve on portion size."),
        
        # 3-star reviews
        Review(customer_name="Rahul Kumar", rating=3.0, comment="Average experience. Food was okay but could be better. Service was decent."),
        Review(customer_name="Meera Singh", rating=3.0, comment="Food was fine but nothing special. Expected more for the price."),
        
        # 2-star reviews
        Review(customer_name="Priya Singh", rating=2.0, comment="Not satisfied with the quality. Food was cold when delivered and taste was below average."),
        
        # 1-star reviews
        Review(customer_name="Arjun Mehta", rating=1.0, comment="Very disappointed. Food was cold, tasteless and delivery took too long. Won't order again.")
    ]

    # Save everything to the database
    db.session.add(vendor)
    db.session.add_all(items)
    db.session.add_all(orders)
    db.session.add_all(reviews)
    db.session.commit()

    print("Database initialized with sample data successfully!")
