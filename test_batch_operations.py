#!/usr/bin/env python3
"""
Test script for batch operations in PrintHub
Tests batch update, batch cancel, and batch delete endpoints
"""
import sys
import time
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Mock Windows modules for testing on Linux
from unittest.mock import MagicMock
sys.modules['win32print'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()

from backend.app import storage
from backend.app.models import BatchOrderUpdate, OrderUpdate


def setup_test_data():
    """Create test orders for batch operations"""
    print("\n=== Setting up test data ===")
    
    # Clear test data
    storage.clear_table("test_batch_orders")
    
    # Create 5 test orders with different statuses
    test_orders = []
    statuses = ["Queued", "Queued", "Printing", "Printing", "Ready"]
    
    for i, status in enumerate(statuses):
        order = {
            "id": f"test-order-{i+1}",
            "studentName": f"Student {i+1}",
            "mobile": f"987654321{i}",
            "fileName": f"test{i+1}.pdf",
            "pages": 10 + i,
            "copies": 1,
            "color": "bw",
            "sides": "single",
            "size": "A4",
            "status": status,
            "paymentStatus": "paid",
            "queueType": "normal",
            "priorityIndex": int(time.time()) - (100 * i),
            "priorityScore": 1.0,
            "priceTotal": 10.0 + i,
            "createdAt": int(time.time()) - 1000,
            "updatedAt": int(time.time()) - 1000,
            "progressPct": 0,
            "assignedPrinterId": None,
            "estimatedSec": None
        }
        storage.insert_one("test_batch_orders", order)
        test_orders.append(order)
    
    print(f"✓ Created {len(test_orders)} test orders")
    return test_orders


def test_batch_update():
    """Test batch update functionality"""
    print("\n=== Testing Batch Update ===")
    
    # Update orders 1-3 to "Cancelled"
    order_ids = ["test-order-1", "test-order-2", "test-order-3"]
    updates = {"status": "Cancelled", "updatedAt": int(time.time())}
    
    count = storage.batch_update_by_ids("test_batch_orders", order_ids, updates)
    
    print(f"✓ Updated {count} orders")
    
    # Verify updates
    for order_id in order_ids:
        order = storage.find_by_id("test_batch_orders", order_id)
        assert order is not None, f"Order {order_id} not found"
        assert order["status"] == "Cancelled", f"Order {order_id} status not updated"
    
    print("✓ All orders updated correctly")
    return count == len(order_ids)


def test_batch_delete():
    """Test batch delete functionality"""
    print("\n=== Testing Batch Delete ===")
    
    # Delete orders 4-5
    order_ids = ["test-order-4", "test-order-5"]
    
    count = storage.batch_delete_by_ids("test_batch_orders", order_ids)
    
    print(f"✓ Deleted {count} orders")
    
    # Verify deletions
    for order_id in order_ids:
        order = storage.find_by_id("test_batch_orders", order_id)
        assert order is None, f"Order {order_id} should be deleted"
    
    print("✓ All orders deleted correctly")
    return count == len(order_ids)


def test_batch_update_performance():
    """Test performance of batch operations vs individual updates"""
    print("\n=== Testing Batch Performance ===")
    
    # Create 100 test orders
    storage.clear_table("test_performance_orders")
    order_ids = []
    
    for i in range(100):
        order = {
            "id": f"perf-order-{i}",
            "studentName": f"Student {i}",
            "mobile": f"9876543210",
            "fileName": f"test{i}.pdf",
            "pages": 10,
            "copies": 1,
            "color": "bw",
            "sides": "single",
            "size": "A4",
            "status": "Queued",
            "paymentStatus": "paid",
            "queueType": "normal",
            "priorityIndex": int(time.time()),
            "priorityScore": 1.0,
            "priceTotal": 10.0,
            "createdAt": int(time.time()),
            "updatedAt": int(time.time()),
            "progressPct": 0,
            "assignedPrinterId": None,
            "estimatedSec": None
        }
        storage.insert_one("test_performance_orders", order)
        order_ids.append(order["id"])
    
    print(f"✓ Created {len(order_ids)} orders for performance test")
    
    # Test individual updates
    start_time = time.time()
    for order_id in order_ids[:50]:
        storage.update_by_id("test_performance_orders", order_id, {"status": "Printing"})
    individual_time = time.time() - start_time
    
    print(f"✓ Individual updates (50 orders): {individual_time:.3f}s")
    
    # Test batch update
    start_time = time.time()
    storage.batch_update_by_ids("test_performance_orders", order_ids[50:], {"status": "Printing"})
    batch_time = time.time() - start_time
    
    print(f"✓ Batch update (50 orders): {batch_time:.3f}s")
    
    # Calculate speedup
    if batch_time > 0:
        speedup = individual_time / batch_time
        print(f"✓ Speedup: {speedup:.1f}x faster")
    else:
        print(f"✓ Batch update was instant (<1ms)")
    
    # Cleanup
    storage.clear_table("test_performance_orders")
    
    return batch_time < individual_time


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    # Test with empty list
    count = storage.batch_update_by_ids("test_batch_orders", [], {"status": "Test"})
    assert count == 0, "Empty list should return 0"
    print("✓ Empty list handled correctly")
    
    # Test with non-existent IDs
    count = storage.batch_update_by_ids("test_batch_orders", ["nonexistent-1", "nonexistent-2"], {"status": "Test"})
    assert count == 0, "Non-existent IDs should return 0"
    print("✓ Non-existent IDs handled correctly")
    
    # Test with mix of existing and non-existing IDs
    count = storage.batch_update_by_ids("test_batch_orders", ["test-order-1", "nonexistent"], {"status": "Ready"})
    assert count >= 1, "Should update at least the existing order"
    print("✓ Mixed IDs handled correctly")
    
    return True


def test_batch_models():
    """Test Pydantic models for batch operations"""
    print("\n=== Testing Batch Models ===")
    
    # Test BatchOrderUpdate model
    batch_update = BatchOrderUpdate(
        orderIds=["order-1", "order-2", "order-3"],
        updates=OrderUpdate(status="Cancelled", progressPct=0)
    )
    
    assert len(batch_update.orderIds) == 3, "Should have 3 order IDs"
    assert batch_update.updates.status == "Cancelled", "Status should be Cancelled"
    print("✓ BatchOrderUpdate model works correctly")
    
    # Test model serialization
    data = batch_update.model_dump()
    assert "orderIds" in data, "Should serialize orderIds"
    assert "updates" in data, "Should serialize updates"
    print("✓ Model serialization works correctly")
    
    return True


def cleanup():
    """Clean up test data"""
    print("\n=== Cleaning up ===")
    storage.clear_table("test_batch_orders")
    storage.clear_table("test_performance_orders")
    print("✓ Test data cleaned up")


def run_all_tests():
    """Run all batch operation tests"""
    print("=" * 60)
    print("PrintHub Batch Operations Tests")
    print("=" * 60)
    
    results = {}
    
    try:
        test_orders = setup_test_data()
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        return False
    
    try:
        results["batch_update"] = test_batch_update()
    except Exception as e:
        print(f"✗ Batch update test failed: {e}")
        results["batch_update"] = False
    
    try:
        results["batch_delete"] = test_batch_delete()
    except Exception as e:
        print(f"✗ Batch delete test failed: {e}")
        results["batch_delete"] = False
    
    try:
        results["batch_performance"] = test_batch_update_performance()
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        results["batch_performance"] = False
    
    try:
        results["edge_cases"] = test_edge_cases()
    except Exception as e:
        print(f"✗ Edge cases test failed: {e}")
        results["edge_cases"] = False
    
    try:
        results["batch_models"] = test_batch_models()
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        results["batch_models"] = False
    
    try:
        cleanup()
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
