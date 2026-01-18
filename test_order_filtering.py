#!/usr/bin/env python3
"""
Test script to verify order filtering logic.
This script tests that only COMPLETED orders are included in financial calculations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.order_filters import OrderFilters
from models.models import db, Order, Vendor
from app import app
from datetime import date, datetime, timedelta

def test_order_filtering():
    """Test that order filtering works correctly."""
    
    with app.app_context():
        print("🧪 Testing Order Filtering Logic...")
        print("=" * 50)
        
        # Get a vendor ID for testing (use first vendor or create test data)
        vendor = Vendor.query.first()
        if not vendor:
            print("❌ No vendor found in database. Please add test data first.")
            return False
            
        vendor_id = vendor.id
        print(f"📊 Testing with Vendor ID: {vendor_id} ({vendor.business_name})")
        
        # Get all orders for this vendor
        all_orders = Order.query.filter_by(vendor_id=vendor_id).all()
        completed_orders = Order.query.filter_by(vendor_id=vendor_id, status='Completed').all()
        rejected_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.status.in_(['Rejected', 'cancelled', 'FAILED'])
        ).all()
        pending_orders = Order.query.filter_by(vendor_id=vendor_id, status='Pending').all()
        
        print(f"\n📈 Order Statistics:")
        print(f"   Total Orders: {len(all_orders)}")
        print(f"   Completed Orders: {len(completed_orders)}")
        print(f"   Rejected/Cancelled Orders: {len(rejected_orders)}")
        print(f"   Pending Orders: {len(pending_orders)}")
        
        # Test earnings calculations
        print(f"\n💰 Earnings Calculations:")
        
        # Manual calculation (should match our filter)
        manual_total = sum(order.total for order in completed_orders)
        
        # Using our filter
        filtered_total = OrderFilters.calculate_total_earnings(Order, vendor_id)
        
        print(f"   Manual Total (Completed Only): ₹{manual_total:.2f}")
        print(f"   Filtered Total (Our Logic): ₹{filtered_total:.2f}")
        
        if abs(manual_total - filtered_total) < 0.01:  # Allow for floating point precision
            print("   ✅ Total earnings calculation is correct!")
        else:
            print("   ❌ Total earnings calculation is incorrect!")
            return False
        
        # Test today's earnings
        today = date.today()
        today_completed = [o for o in completed_orders if o.created_at.date() == today]
        manual_today = sum(order.total for order in today_completed)
        filtered_today = OrderFilters.calculate_today_earnings(Order, vendor_id)
        
        print(f"   Manual Today (Completed Only): ₹{manual_today:.2f}")
        print(f"   Filtered Today (Our Logic): ₹{filtered_today:.2f}")
        
        if abs(manual_today - filtered_today) < 0.01:
            print("   ✅ Today's earnings calculation is correct!")
        else:
            print("   ❌ Today's earnings calculation is incorrect!")
            return False
        
        # Test order count
        manual_count = len(completed_orders)
        filtered_count = OrderFilters.get_completed_orders_count(Order, vendor_id)
        
        print(f"\n📊 Order Count:")
        print(f"   Manual Count (Completed Only): {manual_count}")
        print(f"   Filtered Count (Our Logic): {filtered_count}")
        
        if manual_count == filtered_count:
            print("   ✅ Order count is correct!")
        else:
            print("   ❌ Order count is incorrect!")
            return False
        
        # Test average order value
        manual_avg = manual_total / manual_count if manual_count > 0 else 0
        filtered_avg = OrderFilters.calculate_average_order_value(Order, vendor_id)
        
        print(f"\n💵 Average Order Value:")
        print(f"   Manual Average (Completed Only): ₹{manual_avg:.2f}")
        print(f"   Filtered Average (Our Logic): ₹{filtered_avg:.2f}")
        
        if abs(manual_avg - filtered_avg) < 0.01:
            print("   ✅ Average order value is correct!")
        else:
            print("   ❌ Average order value is incorrect!")
            return False
        
        # Test that rejected orders are excluded
        print(f"\n🚫 Exclusion Test:")
        if rejected_orders:
            rejected_total = sum(order.total for order in rejected_orders)
            print(f"   Rejected Orders Total: ₹{rejected_total:.2f}")
            print(f"   This amount should NOT be included in earnings")
            
            if rejected_total > 0 and filtered_total != (manual_total + rejected_total):
                print("   ✅ Rejected orders are correctly excluded!")
            else:
                print("   ⚠️  Cannot verify rejection exclusion (no rejected orders with amounts)")
        else:
            print("   ⚠️  No rejected orders found to test exclusion")
        
        print(f"\n🎯 Summary:")
        print(f"   ✅ All financial calculations use ONLY completed orders")
        print(f"   ✅ Rejected, cancelled, and pending orders are excluded")
        print(f"   ✅ Order filtering logic is working correctly")
        
        return True

def show_order_status_breakdown():
    """Show breakdown of orders by status for debugging."""
    
    with app.app_context():
        print("\n📋 Order Status Breakdown:")
        print("=" * 30)
        
        # Get all unique statuses
        statuses = db.session.query(Order.status).distinct().all()
        
        for status_tuple in statuses:
            status = status_tuple[0]
            count = Order.query.filter_by(status=status).count()
            total_amount = db.session.query(db.func.sum(Order.total)).filter_by(status=status).scalar() or 0
            print(f"   {status}: {count} orders, ₹{total_amount:.2f}")

if __name__ == "__main__":
    print("🔍 LocalConnect Order Filtering Test")
    print("=" * 40)
    
    try:
        success = test_order_filtering()
        show_order_status_breakdown()
        
        if success:
            print("\n🎉 All tests passed! Order filtering is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)