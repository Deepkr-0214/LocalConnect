import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from models import db, Vendor, MenuItem, Order, Review
from config import Config
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)

# 1. Configure Upload Folder
# This tells Flask where to save the food images
UPLOAD_FOLDER = os.path.join('static', 'images', 'food')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize Database
db.init_app(app)

# Create tables automatically on startup
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def dashboard():
    from datetime import datetime, date
    from sqlalchemy import func, and_
    
    vendor_id = 1  # Default vendor ID for standalone vendor app
    today = date.today()
    
    # Today's Orders - count all orders placed today for this vendor
    todays_orders = Order.query.filter(
        and_(
            Order.vendor_id == vendor_id,
            func.date(Order.date_posted) == today
        )
    ).count()
    
    # Today's Earnings - sum of completed orders today for this vendor
    todays_earnings = db.session.query(func.sum(Order.total)).filter(
        and_(
            Order.vendor_id == vendor_id,
            func.date(Order.date_posted) == today,
            Order.status == 'Completed'
        )
    ).scalar() or 0.0
    
    # Average Rating from order reviews for this vendor
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.review_rating.isnot(None)
        )
    ).scalar() or 0.0
    
    # Pending Orders - orders with status 'Pending' for this vendor
    pending_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').count()
    
    # Recent pending orders for display (limit 6)
    recent_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').order_by(Order.id.desc()).limit(6).all()
    
    # Top menu items for dashboard preview (limit 5) for this vendor
    top_menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).limit(5).all()

    return render_template('dashboard.html',
                           todays_orders=todays_orders,
                           todays_earnings=todays_earnings,
                           avg_rating=round(avg_rating, 1),
                           pending_orders=pending_orders,
                           orders=recent_orders,
                           menu_items=top_menu_items)

@app.route('/orders')
def orders():
    vendor_id = 1  # Default vendor ID for standalone vendor app
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 10 orders per page
    
    # Get paginated orders for this vendor
    orders_pagination = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('orders.html', 
                         orders=orders_pagination.items,
                         pagination=orders_pagination)

@app.route('/menu')
def menu():
    vendor_id = 1  # Default vendor ID for standalone vendor app
    all_items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    return render_template('menu.html', items=all_items)

# --- ADD MENU ITEM ROUTE (With Image Upload) ---
@app.route('/add_item', methods=['POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        sub_name = request.form.get('sub_name')
        category = request.form.get('category')
        price = request.form.get('price')

        # Handle Image File Upload
        file = request.files.get('image')
        filename = 'default.jpg' # Fallback if no image is uploaded

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Create new item in DB with vendor_id set to 1 (default vendor)
        new_item = MenuItem(
            vendor_id=1,
            name=name,
            sub_name=sub_name,
            category=category,
            price=float(price),
            image_file=filename
        )

        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('menu'))

@app.route('/edit_item/<int:item_id>', methods=['POST'])
def edit_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    
    # Update item details
    item.name = request.form.get('name')
    item.sub_name = request.form.get('sub_name')
    item.category = request.form.get('category')
    item.price = float(request.form.get('price'))
    
    # Handle image update
    file = request.files.get('image')
    if file and file.filename != '':
        # Delete old image if it's not the default
        if item.image_file != 'default.jpg':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_file)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # Save new image
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        item.image_file = filename
    
    db.session.commit()
    return redirect(url_for('menu'))

@app.route('/toggle_item/<int:item_id>', methods=['POST'])
def toggle_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    return '', 204 # Returns "No Content" success status

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    item = MenuItem.query.get_or_404(item_id)

    # Optional: Delete the image file from the folder as well
    if item.image_file != 'default.jpg':
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_file)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('menu'))

@app.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    vendor_id = 1  # Default vendor ID for standalone vendor app
    order = Order.query.filter_by(id=order_id, vendor_id=vendor_id).first_or_404()
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    new_status = data.get('status')
    rejection_reason = data.get('rejection_reason', '')
    
    # Update the status directly without changing the names
    if new_status == 'Accepted':
        order.status = 'Completed'  # This will be shown as "Completed" in the Completed tab
        order.rejection_reason = None  # Clear any previous rejection reason
    elif new_status == 'Rejected':
        order.status = 'Rejected'   # This will be shown as "Rejected" in the Rejected tab
        order.rejection_reason = rejection_reason  # Store the rejection reason
    else:
        order.status = new_status
    
    db.session.commit()
    
    # Return JSON response for AJAX requests
    if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        return {'success': True, 'new_status': order.status, 'rejection_reason': order.rejection_reason}, 200
    
    # For non-AJAX requests, stay on the same page
    return redirect(url_for('orders'))

@app.route('/earnings')
def earnings():
    from datetime import datetime, timedelta
    from sqlalchemy import and_, extract, func as sql_func
    
    vendor_id = 1  # Default vendor ID for standalone vendor app
    
    try:
        # Get current date and time periods
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # 1. Total Earnings (all completed orders for this vendor)
        total_earnings = db.session.query(sql_func.sum(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed'
            )
        ).scalar() or 0.0
        
        # 2. This Month Earnings
        month_earnings = db.session.query(sql_func.sum(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed',
                Order.date_posted >= month_start
            )
        ).scalar() or 0.0
        
        # 3. This Week Earnings
        week_earnings = db.session.query(sql_func.sum(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed',
                Order.date_posted >= week_start
            )
        ).scalar() or 0.0
        
        # 4. Today Earnings
        today_earnings = db.session.query(sql_func.sum(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed',
                sql_func.date(Order.date_posted) == today
            )
        ).scalar() or 0.0
        
        # 5. Order statistics
        total_orders = Order.query.filter(Order.vendor_id == vendor_id, Order.status == 'Completed').count()
        completed_orders = total_orders
        pending_orders = Order.query.filter(Order.vendor_id == vendor_id, Order.status == 'Pending').count()
        all_orders_count = Order.query.filter(Order.vendor_id == vendor_id).count()
        completion_rate = (completed_orders / all_orders_count * 100) if all_orders_count > 0 else 0
        
        # 6. Average order value
        avg_order_value = total_earnings / total_orders if total_orders > 0 else 0
        
        # 7. Daily average (simplified)
        first_order = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.date_posted.asc()).first()
        if first_order:
            days_in_business = (now.date() - first_order.date_posted.date()).days + 1
            daily_average = total_earnings / days_in_business if days_in_business > 0 else 0
        else:
            daily_average = 0
        
        # 8. Simple growth calculations (placeholder)
        month_growth = 15.5  # Placeholder
        week_growth = 8.2    # Placeholder
        
        # 9. Top category (simplified)
        top_category = 'Veg'  # Placeholder
        
        # 10. Other metrics (simplified)
        peak_hour = 19
        highest_order = db.session.query(sql_func.max(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed'
            )
        ).scalar() or 0
        
        best_day = db.session.query(sql_func.max(Order.total)).filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed'
            )
        ).scalar() or 0
        
        # 11. Chart data for last 7 days (simplified)
        chart_data = []
        chart_labels = []
        chart_values = []
        
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_earnings = db.session.query(sql_func.sum(Order.total)).filter(
                and_(
                    Order.vendor_id == vendor_id,
                    Order.status == 'Completed',
                    sql_func.date(Order.date_posted) == date
                )
            ).scalar() or 0
            
            chart_labels.append(date.strftime('%d %b'))
            chart_values.append(float(day_earnings))
        
        # 12. Category data (simplified)
        category_labels = ['Veg', 'Non-Veg', 'Beverages']
        category_values = [float(total_earnings * 0.6), float(total_earnings * 0.3), float(total_earnings * 0.1)]
        
        # 13. Recent transactions
        recent_transactions = Order.query.filter(
            and_(
                Order.vendor_id == vendor_id,
                Order.status == 'Completed'
            )
        ).order_by(Order.date_posted.desc()).limit(5).all()
        
        # 14. Earnings history
        earnings_history = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.date_posted.desc()).limit(50).all()
        
        return render_template('earnings_simple.html',
                               total_earnings=total_earnings,
                               month_earnings=month_earnings,
                               week_earnings=week_earnings,
                               today_earnings=today_earnings,
                               month_growth=month_growth,
                               week_growth=week_growth,
                               total_orders=total_orders,
                               completed_orders=completed_orders,
                               pending_orders=pending_orders,
                               completion_rate=completion_rate,
                               avg_order_value=avg_order_value,
                               daily_average=daily_average,
                               top_category=top_category,
                               peak_hour=peak_hour,
                               highest_order=highest_order,
                               best_day=best_day,
                               chart_labels=chart_labels,
                               chart_values=chart_values,
                               category_labels=category_labels,
                               category_values=category_values,
                               recent_transactions=recent_transactions,
                               earnings_history=earnings_history)
    
    except Exception as e:
        print(f"Error in earnings route: {e}")
        # Return with default values if there's an error
        return render_template('earnings_simple.html',
                               total_earnings=0,
                               month_earnings=0,
                               week_earnings=0,
                               today_earnings=0,
                               month_growth=0,
                               week_growth=0,
                               total_orders=0,
                               completed_orders=0,
                               pending_orders=0,
                               completion_rate=0,
                               avg_order_value=0,
                               daily_average=0,
                               top_category='N/A',
                               peak_hour=19,
                               highest_order=0,
                               best_day=0,
                               chart_labels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                               chart_values=[0, 0, 0, 0, 0, 0, 0],
                               category_labels=['Veg', 'Non-Veg'],
                               category_values=[0, 0],
                               recent_transactions=[],
                               earnings_history=[])

@app.route('/reviews')
def reviews():
    from datetime import datetime, timedelta
    from sqlalchemy import and_
    
    vendor_id = 1  # Default vendor ID for standalone vendor app
    filter_type = request.args.get('filter', 'all')
    
    # Base query - get orders with reviews for this vendor
    query = Order.query.filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.review_rating.isnot(None)
        )
    )
    
    # Apply filters
    if filter_type == '5':
        query = query.filter(Order.review_rating == 5)
    elif filter_type == '4':
        query = query.filter(Order.review_rating == 4)
    elif filter_type == '3':
        query = query.filter(Order.review_rating == 3)
    elif filter_type == '2':
        query = query.filter(Order.review_rating == 2)
    elif filter_type == '1':
        query = query.filter(Order.review_rating == 1)
    
    filtered_reviews = query.order_by(Order.review_date.desc()).all()
    
    # Calculate metrics for all reviews (not filtered) for this vendor
    avg_rating = db.session.query(func.avg(Order.review_rating)).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.review_rating.isnot(None)
        )
    ).scalar() or 0.0
    
    total_count = Order.query.filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.review_rating.isnot(None)
        )
    ).count()
    
    current_month = datetime.now().replace(day=1)
    recent_count = Order.query.filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.review_rating.isnot(None),
            Order.review_date >= current_month
        )
    ).count()
    
    # For vendor reviews, response functionality is not implemented
    responded_count = 0
    response_rate = 0
    
    five_star_count = Order.query.filter(Order.vendor_id == vendor_id, Order.review_rating == 5).count()
    four_star_count = Order.query.filter(Order.vendor_id == vendor_id, Order.review_rating == 4).count()
    three_star_count = Order.query.filter(Order.vendor_id == vendor_id, Order.review_rating == 3).count()
    two_star_count = Order.query.filter(Order.vendor_id == vendor_id, Order.review_rating == 2).count()
    one_star_count = Order.query.filter(Order.vendor_id == vendor_id, Order.review_rating == 1).count()
    pending_count = 0

    return render_template('reviews_system.html',
                           reviews=filtered_reviews,
                           current_filter=filter_type,
                           avg_rating=round(avg_rating, 1),
                           total_count=total_count,
                           recent_count=recent_count,
                           responded_count=responded_count,
                           response_rate=round(response_rate, 1),
                           five_star_count=five_star_count,
                           four_star_count=four_star_count,
                           three_star_count=three_star_count,
                           two_star_count=two_star_count,
                           one_star_count=one_star_count,
                           pending_count=pending_count)

@app.route('/toggle_shop_status', methods=['POST'])
def toggle_shop_status():
    import json
    data = request.get_json()
    is_open = data.get('is_open', False)
    
    vendor = Vendor.query.first()
    if not vendor:
        vendor = Vendor()
        db.session.add(vendor)
    
    vendor.is_open = is_open
    db.session.commit()
    
    return json.dumps({'success': True, 'is_open': is_open})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    vendor = Vendor.query.first()
    if not vendor:
        vendor = Vendor()
        db.session.add(vendor)

    # Update fields from the settings form
    vendor.shop_name = request.form.get('shop_name')
    vendor.email = request.form.get('email')
    vendor.phone = request.form.get('phone')
    vendor.address = request.form.get('address')
    vendor.is_open = 'is_open' in request.form

    db.session.commit()
    flash("Profile updated successfully!")
    return redirect(url_for('settings'))

@app.route('/settings')
def settings():
    vendor_info = Vendor.query.first()
    return render_template('settings.html', vendor=vendor_info)

@app.route('/logout')
def logout():
    flash("Logged out successfully!")
    return redirect(url_for('dashboard'))

@app.context_processor
def inject_vendor_info():
    # Fetch the first vendor in the database (the shop owner)
    vendor = Vendor.query.first()
    # For now, set unread_count to 0 as there's no notification system yet
    unread_count = 0
    return dict(vendor_profile=vendor, unread_count=unread_count)
    

if __name__ == '__main__':
    app.run(debug=True, port=5001)
