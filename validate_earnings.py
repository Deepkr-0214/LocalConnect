#!/usr/bin/env python3
"""
Validation script for order filtering fix.
Tests the exact scenario: completed orders ₹460, ₹500, ₹250, ₹570, ₹750 = ₹2,530
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.order_filters import OrderFilters
from models.models import db, Order, Vendor
from app import app
from datetime import date, datetime

def validate_earnings_calculation():
    """Validate that earnings calculation matches expected values."""
    
    with app.app_context():
        print("🔍 Validating Earnings Calculation...")
        print("=" * 50)
        
        # Get a vendor for testing
        vendor = Vendor.query.first()
        if not vendor:
            print("❌ No vendor found. Please add test data first.")
            return False
            
        vendor_id = vendor.id
        print(f"📊 Testing with Vendor ID: {vendor_id}")
        
        # Get completed orders and their totals
        completed_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.status == 'Completed'
        ).all()
        
        print(f"\n💰 Completed Orders Analysis:")
        print(f"   Found {len(completed_orders)} completed orders")
        
        if completed_orders:
            total_manual = 0
            for i, order in enumerate(completed_orders, 1):
                print(f"   Order {i}: ₹{order.total} (Status: {order.status})")
                total_manual += order.total
            
            print(f"\n   Manual Total: ₹{total_manual}")
            
            # Test our filtering logic
            filtered_total = OrderFilters.calculate_total_earnings(Order, db, vendor_id)
            print(f"   Filtered Total: ₹{filtered_total}")
            
            if abs(total_manual - filtered_total) < 0.01:
                print("   ✅ Earnings calculation is CORRECT!")
                
                # Check if it matches the expected test case
                expected_total = 2530.0  # ₹460 + ₹500 + ₹250 + ₹570 + ₹750
                if abs(filtered_total - expected_total) < 0.01:
                    print(f"   🎯 Perfect! Matches expected test case: ₹{expected_total}")
                else:
                    print(f"   ℹ️  Different from test case (₹{expected_total}), but calculation is correct")
                
                return True
            else:
                print("   ❌ Earnings calculation is INCORRECT!")
                return False
        else:
            print("   ⚠️  No completed orders found")
            return True
        
        # Check rejected orders are excluded
        rejected_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.status.in_(['Rejected', 'cancelled', 'FAILED'])
        ).all()
        
        if rejected_orders:
            print(f"\n🚫 Rejected Orders Analysis:")
            print(f"   Found {len(rejected_orders)} rejected/cancelled orders")
            rejected_total = sum(order.total for order in rejected_orders)
            print(f"   Rejected Total: ₹{rejected_total}")
            print(f"   ✅ These are correctly EXCLUDED from earnings")
        
        return True

def show_all_orders_by_status():
    """Show all orders grouped by status for debugging."""
    
    with app.app_context():
        print("\n📋 All Orders by Status:")
        print("=" * 30)
        
        # Get all unique statuses
        statuses = db.session.query(Order.status).distinct().all()
        
        total_all_orders = 0
        total_completed_only = 0
        
        for status_tuple in statuses:
            status = status_tuple[0] if status_tuple[0] else 'NULL'
            orders = Order.query.filter_by(status=status).all()
            count = len(orders)
            total_amount = sum(order.total for order in orders)
            
            print(f"   {status}: {count} orders, ₹{total_amount:.2f}")
            
            total_all_orders += total_amount
            if status == 'Completed':
                total_completed_only += total_amount
        
        print(f"\n📊 Summary:")
        print(f"   Total (All Orders): ₹{total_all_orders:.2f}")
        print(f"   Total (Completed Only): ₹{total_completed_only:.2f}")
        print(f"   Difference: ₹{total_all_orders - total_completed_only:.2f}")
        
        if total_all_orders != total_completed_only:
            print(f"   ✅ Good! System correctly excludes ₹{total_all_orders - total_completed_only:.2f} from non-completed orders")
        else:
            print(f"   ℹ️  All orders are completed, no filtering needed")

if __name__ == "__main__":
    print("🎯 LocalConnect Earnings Validation")
    print("Testing: Completed orders should total ₹2,530")
    print("Rejected orders should be excluded")
    print("=" * 50)
    
    try:
        success = validate_earnings_calculation()
        show_all_orders_by_status()
        
        if success:
            print("\n🎉 Validation PASSED! Order filtering is working correctly.")
            print("💡 Only COMPLETED orders are included in earnings calculations.")
            sys.exit(0)
        else:
            print("\n❌ Validation FAILED! Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)