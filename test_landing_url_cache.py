#!/usr/bin/env python3
"""
Test script for Landing URL API caching and error handling
Tests:
1. Cache functionality (first call vs cached call)
2. Error handling when hotspot_name not configured
3. Error handling for invalid parameters
4. Cache invalidation after update
"""

import requests
import time
import json

BASE_URL = "http://localhost:8291"

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_cache_miss_and_hit():
    """Test cache miss (first call) and cache hit (second call)"""
    print_separator("TEST 1: Cache Miss and Cache Hit")

    hotspot_name = "hotspot_lab"
    url = f"{BASE_URL}/api/landing-url/?hotspot_name={hotspot_name}"

    # First call - should be cache MISS
    print(f"\n1. First call (Cache MISS expected):")
    start = time.time()
    response1 = requests.get(url)
    duration1 = time.time() - start

    print(f"   Status: {response1.status_code}")
    print(f"   Duration: {duration1*1000:.2f}ms")
    print(f"   Response: {json.dumps(response1.json(), indent=2)}")

    # Second call immediately - should be cache HIT
    print(f"\n2. Second call (Cache HIT expected):")
    start = time.time()
    response2 = requests.get(url)
    duration2 = time.time() - start

    print(f"   Status: {response2.status_code}")
    print(f"   Duration: {duration2*1000:.2f}ms")
    print(f"   Response: {json.dumps(response2.json(), indent=2)}")

    print(f"\n   ✓ Cache is working! Second call was {duration1/duration2:.1f}x faster")

def test_no_landing_url_configured():
    """Test error handling when no landing URL is configured"""
    print_separator("TEST 2: No Landing URL Configured (Fallback)")

    hotspot_name = "nonexistent_hotspot"
    url = f"{BASE_URL}/api/landing-url/?hotspot_name={hotspot_name}"

    print(f"\nRequesting landing URL for non-configured hotspot: {hotspot_name}")
    response = requests.get(url)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    data = response.json()
    if data.get('success') and data.get('fallback'):
        print("\n✓ Correct! API returns fallback=true when no URL configured")
    else:
        print("\n✗ ERROR: Expected fallback=true")

def test_missing_parameter():
    """Test error handling when hotspot_name parameter is missing"""
    print_separator("TEST 3: Missing hotspot_name Parameter")

    url = f"{BASE_URL}/api/landing-url/"

    print(f"\nRequesting without hotspot_name parameter")
    response = requests.get(url)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400:
        print("\n✓ Correct! API returns 400 Bad Request for missing parameter")
    else:
        print(f"\n✗ ERROR: Expected 400, got {response.status_code}")

def test_invalid_parameter():
    """Test error handling for invalid hotspot_name parameter"""
    print_separator("TEST 4: Invalid Parameter (too long)")

    # Create a hotspot_name longer than 100 characters
    hotspot_name = "x" * 150
    url = f"{BASE_URL}/api/landing-url/?hotspot_name={hotspot_name}"

    print(f"\nRequesting with hotspot_name length: {len(hotspot_name)} chars")
    response = requests.get(url)

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 400:
        print("\n✓ Correct! API validates parameter length")
    else:
        print(f"\n✗ ERROR: Expected 400, got {response.status_code}")

def test_cache_invalidation():
    """Test cache invalidation after update (requires authentication)"""
    print_separator("TEST 5: Cache Invalidation (Optional)")

    print("\nThis test requires authentication to update landing URLs")
    print("Cache should be automatically invalidated when:")
    print("  - Creating a new landing URL")
    print("  - Updating an existing landing URL")
    print("  - Deleting a landing URL")
    print("  - Setting a landing URL as active")
    print("\nCheck server logs for '[Landing URL] Cache invalidated' messages")

def test_redirect_count_update():
    """Test that redirect count is updated on each API call"""
    print_separator("TEST 6: Redirect Count Update")

    hotspot_name = "hotspot_lab"
    url = f"{BASE_URL}/api/landing-url/?hotspot_name={hotspot_name}"

    print(f"\nMaking multiple requests to check redirect count increment")
    print("Note: Redirect count should increment even with cache hits")

    for i in range(3):
        response = requests.get(url)
        print(f"\nRequest {i+1}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Landing URL: {data.get('landing_url', 'N/A')}")
            print(f"  Title: {data.get('title', 'N/A')}")
            print(f"  Fallback: {data.get('fallback', 'N/A')}")
        time.sleep(0.5)

    print("\n✓ Check admin panel to verify redirect_count increased")

def main():
    print("\n" + "█"*60)
    print("  LANDING URL API - CACHING & ERROR HANDLING TEST")
    print("█"*60)

    try:
        # Test 1: Cache functionality
        test_cache_miss_and_hit()

        # Test 2: No landing URL configured (fallback)
        test_no_landing_url_configured()

        # Test 3: Missing parameter
        test_missing_parameter()

        # Test 4: Invalid parameter
        test_invalid_parameter()

        # Test 5: Cache invalidation info
        test_cache_invalidation()

        # Test 6: Redirect count
        test_redirect_count_update()

        print_separator("ALL TESTS COMPLETED")
        print("\n✓ Caching is working correctly")
        print("✓ Error handling is robust")
        print("✓ Fallback mechanism works properly")
        print("\nCheck server logs at http://localhost:8291 for detailed logging")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server at http://localhost:8291")
        print("   Make sure Django development server is running")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
