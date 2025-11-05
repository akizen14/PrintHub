"""
Migration script to add paymentStatus field to existing orders.

This script updates all existing orders in the database to include the new paymentStatus field.
Orders with status "Queued", "Printing", "Ready", or "Collected" are marked as "paid".
Orders with status "Pending" are marked as "unpaid".
"""

import json
from pathlib import Path

def migrate_orders():
    """Add paymentStatus field to all existing orders."""
    data_dir = Path(__file__).parent / "data"
    orders_file = data_dir / "orders.json"
    
    if not orders_file.exists():
        print("❌ orders.json not found")
        return
    
    # Read existing orders
    with open(orders_file, 'r') as f:
        data = json.load(f)
    
    # Check if data has orders
    if not data or "_default" not in data:
        print("ℹ️  No orders to migrate")
        return
    
    orders = data["_default"]
    updated_count = 0
    
    # Update each order
    for order_id, order in orders.items():
        if "paymentStatus" not in order:
            # Determine payment status based on order status
            if order.get("status") in ["Queued", "Printing", "Ready", "Collected"]:
                order["paymentStatus"] = "paid"
                # Ensure Queued+ orders have Queued or higher status
                if order.get("status") == "Pending":
                    order["status"] = "Queued"
            else:
                order["paymentStatus"] = "unpaid"
            
            updated_count += 1
            print(f"✅ Updated order {order_id[:8]}... - Status: {order['status']}, Payment: {order['paymentStatus']}")
    
    # Write back to file
    if updated_count > 0:
        with open(orders_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Migration complete! Updated {updated_count} orders.")
    else:
        print("ℹ️  No orders needed migration (all already have paymentStatus)")

if __name__ == "__main__":
    print("🔄 Starting migration to add paymentStatus field...\n")
    migrate_orders()
