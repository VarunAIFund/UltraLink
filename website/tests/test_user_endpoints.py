"""
Test script for Phase 2 user workspace endpoints
Run this after starting the backend with: python app.py
Usage: python test_user_endpoints.py
"""
import requests
import json
from urllib.parse import quote

BASE_URL = "http://localhost:5000"

# Track test results
test_results = []

def print_test(test_num, description):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"Test {test_num}: {description}")
    print('='*60)

def print_result(response):
    """Print formatted JSON response"""
    try:
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Response: {response.text}")

def check_test(test_name, condition, expected_status, actual_status):
    """Check if test passed and record result"""
    passed = condition and (expected_status == actual_status)
    test_results.append({
        'name': test_name,
        'passed': passed,
        'expected': expected_status,
        'actual': actual_status
    })
    return passed

def main():
    print("\n" + "="*60)
    print("PHASE 2 ENDPOINT TESTING")
    print("="*60)

    # Test 1: Get all users
    print_test(1, "GET /users")
    response = requests.get(f"{BASE_URL}/users")
    print_result(response)
    check_test("GET /users", response.json().get('success'), 200, response.status_code)

    # Test 2: Get specific user (linda)
    print_test(2, "GET /users/linda")
    response = requests.get(f"{BASE_URL}/users/linda")
    print_result(response)
    check_test("GET /users/linda", response.json().get('success'), 200, response.status_code)

    # Test 3: Get invalid user (should return 404)
    print_test(3, "GET /users/invalid (should fail)")
    response = requests.get(f"{BASE_URL}/users/invalid")
    print_result(response)
    check_test("GET /users/invalid", not response.json().get('success'), 404, response.status_code)

    # Test 4: Search with user_name
    print_test(4, "POST /search-and-rank with user_name=linda")
    response = requests.post(
        f"{BASE_URL}/search-and-rank",
        json={
            "query": "stanford grad cs who worked at google ",
            "connected_to": "linda",
            "user_name": "linda"
        }
    )
    print_result(response)
    check_test("POST /search-and-rank with user_name", response.json().get('success'), 200, response.status_code)

    # Save search_id for later tests
    search_id = None
    try:
        search_id = response.json().get('id')
        print(f"\n✓ Search ID: {search_id}")
    except:
        pass

    # Test 5: Get user's search history
    print_test(5, "GET /users/linda/searches")
    response = requests.get(f"{BASE_URL}/users/linda/searches")
    print_result(response)
    check_test("GET /users/<username>/searches", response.json().get('success'), 200, response.status_code)

    # Test 6: Add bookmark
    print_test(6, "POST /users/linda/bookmarks")
    linkedin_url = "https://www.linkedin.com/in/test-candidate/"
    response = requests.post(
        f"{BASE_URL}/users/linda/bookmarks",
        json={
            "linkedin_url": linkedin_url,
            "candidate_name": "Test Candidate",
            "candidate_headline": "Software Engineer at Test Company",
            "notes": "Great candidate for our team!"
        }
    )
    print_result(response)
    check_test("POST /users/<username>/bookmarks", response.json().get('success'), 200, response.status_code)

    # Test 7: Check if bookmarked
    print_test(7, "GET /users/linda/bookmarks/check/...")
    encoded_url = quote(linkedin_url, safe='')
    response = requests.get(f"{BASE_URL}/users/linda/bookmarks/check/{encoded_url}")
    print_result(response)
    check_test("GET /users/<username>/bookmarks/check", response.json().get('success') and response.json().get('is_bookmarked'), 200, response.status_code)

    # Test 8: Get all bookmarks
    print_test(8, "GET /users/linda/bookmarks")
    response = requests.get(f"{BASE_URL}/users/linda/bookmarks")
    print_result(response)
    check_test("GET /users/<username>/bookmarks", response.json().get('success'), 200, response.status_code)

    # Test 9: Remove bookmark
    print_test(9, "DELETE /users/linda/bookmarks/...")
    response = requests.delete(f"{BASE_URL}/users/linda/bookmarks/{encoded_url}")
    print_result(response)
    check_test("DELETE /users/<username>/bookmarks", response.json().get('success'), 200, response.status_code)

    # Test 10: Verify bookmark was removed
    print_test(10, "Verify bookmark removed")
    response = requests.get(f"{BASE_URL}/users/linda/bookmarks/check/{encoded_url}")
    print_result(response)
    check_test("Verify bookmark removed", response.json().get('success') and not response.json().get('is_bookmarked'), 200, response.status_code)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for t in test_results if t['passed'])
    failed = len(test_results) - passed

    for i, test in enumerate(test_results, 1):
        status = "✅ PASS" if test['passed'] else "❌ FAIL"
        print(f"{i}. {status} - {test['name']} (expected {test['expected']}, got {test['actual']})")

    print("\n" + "="*60)
    if failed == 0:
        print(f"🎉 ALL {passed} TESTS PASSED!")
    else:
        print(f"⚠️  {passed} PASSED, {failed} FAILED")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend.")
        print("Make sure the backend is running: python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
