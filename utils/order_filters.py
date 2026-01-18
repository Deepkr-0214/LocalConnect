"""
Order filtering utilities for financial calculations.
Ensures only COMPLETED orders are included in earnings and analytics.
"""

from sqlalchemy import func, and_
from datetime import date, timedelta


class OrderFilters:
    """Centralized order filtering logic for financial calculations."""
    
    COMPLETED_STATUS = 'Completed'
    EXCLUDED_STATUSES = ['Rejected', 'cancelled', 'FAILED', 'Pending', 'preparing', 'ready', 'out_for_delivery']
    
    @staticmethod
    def get_completed_orders_query(Order, vendor_id):
        """Get base query for completed orders only."""
        return Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS
        )
    
    @staticmethod
    def calculate_total_earnings(Order, db, vendor_id):
        """Calculate total earnings from completed orders only using DB aggregation."""
        result = db.session.query(func.sum(Order.total)).filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS
        ).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def calculate_today_earnings(Order, db, vendor_id):
        """Calculate today's earnings from completed orders only using DB aggregation."""
        today = date.today()
        result = db.session.query(func.sum(Order.total)).filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS,
            func.date(Order.created_at) == today
        ).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def calculate_week_earnings(Order, db, vendor_id):
        """Calculate this week's earnings from completed orders only using DB aggregation."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        result = db.session.query(func.sum(Order.total)).filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS,
            func.date(Order.created_at) >= week_start
        ).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def calculate_month_earnings(Order, db, vendor_id):
        """Calculate this month's earnings from completed orders only using DB aggregation."""
        today = date.today()
        month_start = today.replace(day=1)
        result = db.session.query(func.sum(Order.total)).filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS,
            func.date(Order.created_at) >= month_start
        ).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def get_completed_orders_count(Order, vendor_id):
        """Get count of completed orders only."""
        return Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS
        ).count()
    
    @staticmethod
    def calculate_average_order_value(Order, db, vendor_id):
        """Calculate average order value from completed orders only using DB aggregation."""
        result = db.session.query(func.avg(Order.total)).filter(
            Order.vendor_id == vendor_id,
            Order.status == OrderFilters.COMPLETED_STATUS
        ).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def get_earnings_chart_data(Order, db, vendor_id, days=7):
        """Get earnings data for chart (last N days) from completed orders only using DB aggregation."""
        today = date.today()
        chart_labels = []
        chart_values = []
        
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime('%d %b'))
            
            day_earnings = db.session.query(func.sum(Order.total)).filter(
                Order.vendor_id == vendor_id,
                Order.status == OrderFilters.COMPLETED_STATUS,
                func.date(Order.created_at) == day
            ).scalar()
            
            chart_values.append(float(day_earnings) if day_earnings else 0.0)
        
        return chart_labels, chart_values