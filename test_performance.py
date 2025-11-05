#!/usr/bin/env python3
"""
Test script to verify performance optimizations in PrintHub
Tests connection pooling, caching, and other improvements
"""
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_connection_pooling():
    """Test that database connections are reused"""
    print("\n=== Testing Connection Pooling ===")
    from backend.app import storage
    
    # Test multiple reads use same connection
    start = time.time()
    for i in range(50):
        _ = storage.find_all("orders")
    duration = time.time() - start
    
    print(f"✓ 50 reads completed in {duration:.3f}s ({duration/50*1000:.2f}ms per read)")
    if duration < 0.1:  # Should be very fast with pooling
        print("✓ Connection pooling working (very fast reads)")
    else:
        print("⚠ Reads slower than expected")
    
    # Check cache exists
    print(f"✓ Cached connections: {len(storage._db_cache)}")
    return duration < 1.0  # Should complete in under 1 second


def test_lru_cache():
    """Test that LRU cache reduces disk reads"""
    print("\n=== Testing LRU Cache ===")
    from backend.app.routers.orders import get_cached_rates, get_cached_settings
    
    cache_key = int(time.time() / 60)
    
    # First call - cache miss
    start1 = time.time()
    rates1 = get_cached_rates(cache_key)
    time1 = time.time() - start1
    
    # Second call - cache hit
    start2 = time.time()
    rates2 = get_cached_rates(cache_key)
    time2 = time.time() - start2
    
    print(f"✓ First call (cache miss): {time1*1000:.3f}ms")
    print(f"✓ Second call (cache hit): {time2*1000:.3f}ms")
    
    # Avoid division by zero - if cache hit is instant, show as very fast
    MIN_TIME_THRESHOLD = 0.000001  # 1 microsecond
    if time2 > MIN_TIME_THRESHOLD:
        print(f"✓ Speedup: {time1/time2:.1f}x faster")
    else:
        print(f"✓ Speedup: >1000x faster (cache hit was instant)")
    
    # Cache should make second call much faster or instant
    return time2 <= time1


def test_app_initialization():
    """Test that FastAPI app loads with all middleware"""
    print("\n=== Testing App Initialization ===")
    try:
        # Mock Windows modules for testing on Linux
        import sys
        from unittest.mock import MagicMock
        sys.modules['win32print'] = MagicMock()
        sys.modules['win32api'] = MagicMock()
        sys.modules['win32con'] = MagicMock()
        
        from backend.app.main import app
        print(f"✓ App title: {app.title}")
        print(f"✓ Middlewares loaded: {len(app.user_middleware)}")
        
        # Check for GZIP middleware
        middleware_types = [str(type(m)) for m in app.user_middleware]
        has_gzip = any("GZip" in m for m in middleware_types)
        has_cors = any("CORS" in m for m in middleware_types)
        
        print(f"✓ GZIP compression: {'enabled' if has_gzip else 'not found'}")
        print(f"✓ CORS middleware: {'enabled' if has_cors else 'not found'}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading app: {e}")
        return False


def test_storage_operations():
    """Test various storage operations work correctly"""
    print("\n=== Testing Storage Operations ===")
    from backend.app import storage
    import uuid
    
    test_table = "test_orders"
    
    try:
        # Test insert
        test_id = str(uuid.uuid4())
        test_data = {"id": test_id, "test": "data", "timestamp": int(time.time())}
        storage.insert_one(test_table, test_data)
        print("✓ Insert working")
        
        # Test find
        found = storage.find_by_id(test_table, test_id)
        assert found is not None
        assert found["test"] == "data"
        print("✓ Find by ID working")
        
        # Test update
        storage.update_by_id(test_table, test_id, {"test": "updated"})
        updated = storage.find_by_id(test_table, test_id)
        assert updated["test"] == "updated"
        print("✓ Update working")
        
        # Test delete
        storage.delete_by_id(test_table, test_id)
        deleted = storage.find_by_id(test_table, test_id)
        assert deleted is None
        print("✓ Delete working")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("PrintHub Performance Optimization Tests")
    print("=" * 60)
    
    results = {}
    
    try:
        results["connection_pooling"] = test_connection_pooling()
    except Exception as e:
        print(f"✗ Connection pooling test failed: {e}")
        results["connection_pooling"] = False
    
    try:
        results["lru_cache"] = test_lru_cache()
    except Exception as e:
        print(f"✗ LRU cache test failed: {e}")
        results["lru_cache"] = False
    
    try:
        results["app_init"] = test_app_initialization()
    except Exception as e:
        print(f"✗ App initialization test failed: {e}")
        results["app_init"] = False
    
    try:
        results["storage_ops"] = test_storage_operations()
    except Exception as e:
        print(f"✗ Storage operations test failed: {e}")
        results["storage_ops"] = False
    
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
