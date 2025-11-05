"""
Test script for payment UPI integration.

This tests the complete flow:
1. Create an order (should be Pending with unpaid status)
2. Confirm payment (should move to Queued with paid status)
3. Verify admin can see only paid orders
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")

def test_create_order():
    """Test creating an order."""
    print_header("TEST 1: Create Order")
    
    order_data = {
        "studentName": "Test Student",
        "mobile": "1234567890",
        "fileName": "test.pdf",
        "pages": 5,
        "copies": 1,
        "color": "bw",
        "sides": "single",
        "size": "A4",
    }
    
    try:
        response = requests.post(f"{API_BASE}/orders", json=order_data)
        response.raise_for_status()
        order = response.json()
        
        print(f"✅ Order created successfully!")
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        print(f"   Payment Status: {order['paymentStatus']}")
        print(f"   Price: ₹{order['priceTotal']}")
        
        # Verify initial state
        assert order['status'] == 'Pending', f"Expected status 'Pending', got '{order['status']}'"
        assert order['paymentStatus'] == 'unpaid', f"Expected payment status 'unpaid', got '{order['paymentStatus']}'"
        
        print("\n✅ Order has correct initial state (Pending + unpaid)")
        return order['id']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create order: {e}")
        return None
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return None

def test_confirm_payment(order_id):
    """Test confirming payment for an order."""
    print_header("TEST 2: Confirm Payment")
    
    if not order_id:
        print("❌ No order ID provided")
        return False
    
    try:
        response = requests.post(f"{API_BASE}/orders/{order_id}/confirm-payment")
        response.raise_for_status()
        order = response.json()
        
        print(f"✅ Payment confirmed successfully!")
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        print(f"   Payment Status: {order['paymentStatus']}")
        
        # Verify payment confirmed state
        assert order['status'] == 'Queued', f"Expected status 'Queued', got '{order['status']}'"
        assert order['paymentStatus'] == 'paid', f"Expected payment status 'paid', got '{order['paymentStatus']}'"
        
        print("\n✅ Order moved to queue after payment (Queued + paid)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to confirm payment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Error details: {e.response.text}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False

def test_admin_queue_filter():
    """Test that admin only sees paid orders."""
    print_header("TEST 3: Admin Queue Filter")
    
    try:
        # Get all orders with Queued status (what admin sees)
        response = requests.get(f"{API_BASE}/orders?status=Queued|Printing|Ready")
        response.raise_for_status()
        queued_orders = response.json()
        
        print(f"📋 Orders in admin queue: {len(queued_orders)}")
        
        # Verify all queued orders are paid
        all_paid = all(order.get('paymentStatus') == 'paid' for order in queued_orders)
        
        if all_paid:
            print("✅ All orders in admin queue are paid")
            for order in queued_orders[:3]:  # Show first 3
                print(f"   - {order['studentName']}: {order['status']} / {order['paymentStatus']}")
        else:
            print("❌ Found unpaid orders in admin queue!")
            return False
        
        # Get pending orders (should have unpaid)
        response = requests.get(f"{API_BASE}/orders?status=Pending")
        response.raise_for_status()
        pending_orders = response.json()
        
        print(f"\n📋 Pending orders (not in queue): {len(pending_orders)}")
        for order in pending_orders[:3]:  # Show first 3
            print(f"   - {order['studentName']}: {order['status']} / {order['paymentStatus']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get orders: {e}")
        return False

def test_double_payment_confirmation(order_id):
    """Test that confirming payment twice fails appropriately."""
    print_header("TEST 4: Prevent Double Payment Confirmation")
    
    if not order_id:
        print("❌ No order ID provided")
        return False
    
    try:
        response = requests.post(f"{API_BASE}/orders/{order_id}/confirm-payment")
        
        # Should get 400 error for already paid order
        if response.status_code == 400:
            error = response.json()
            print(f"✅ Correctly prevented double payment confirmation")
            print(f"   Error message: {error.get('detail', 'Unknown error')}")
            return True
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  PAYMENT UPI INTEGRATION TESTS")
    print("=" * 60)
    print("\nTesting payment flow: Order → UPI → Confirm → Queue\n")
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Backend is running at {API_BASE}")
    except requests.exceptions.RequestException:
        print(f"❌ Backend is not running at {API_BASE}")
        print("   Please start the backend with: cd backend && uvicorn app.main:app --reload")
        return
    
    # Run tests
    test_results = []
    
    # Test 1: Create order
    order_id = test_create_order()
    test_results.append(("Create Order", order_id is not None))
    
    if order_id:
        # Wait a bit for the database to settle
        time.sleep(0.5)
        
        # Test 2: Confirm payment
        payment_confirmed = test_confirm_payment(order_id)
        test_results.append(("Confirm Payment", payment_confirmed))
        
        # Wait a bit
        time.sleep(0.5)
        
        # Test 3: Admin queue filter
        queue_filtered = test_admin_queue_filter()
        test_results.append(("Admin Queue Filter", queue_filtered))
        
        # Test 4: Prevent double confirmation
        if payment_confirmed:
            double_prevented = test_double_payment_confirmation(order_id)
            test_results.append(("Prevent Double Confirmation", double_prevented))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 60}\n")
    
    if passed == total:
        print("🎉 All tests passed! Payment integration working correctly.\n")
    else:
        print("⚠️  Some tests failed. Please check the output above.\n")

if __name__ == "__main__":
    main()
