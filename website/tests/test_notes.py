"""
Test script for candidate notes functionality
Tests adding, updating, and retrieving notes for candidates
"""
import requests
import json

# Backend URL
BASE_URL = "http://localhost:5000"

def test_add_note():
    """Test adding a note to a candidate"""
    print("\n" + "="*60)
    print("TEST 1: Add note to candidate")
    print("="*60)

    # Use a real LinkedIn URL from your database
    test_url = "https://www.linkedin.com/in/ppzhao"
    test_note = "Great candidate! Strong Python skills. Follow up next week."

    response = requests.post(
        f"{BASE_URL}/notes",
        json={
            "linkedin_url": test_url,
            "note": test_note
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Note added successfully!")
    else:
        print("❌ Failed to add note")

    return response.json()

def test_get_note():
    """Test retrieving a note for a candidate"""
    print("\n" + "="*60)
    print("TEST 2: Get note for candidate")
    print("="*60)

    # Use the same LinkedIn URL
    test_url = "https://www.linkedin.com/in/test-profile/"

    # URL encode the LinkedIn URL for the GET request
    from urllib.parse import quote
    encoded_url = quote(test_url, safe='')

    response = requests.get(f"{BASE_URL}/notes/{encoded_url}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Note retrieved successfully!")
    else:
        print("❌ Failed to retrieve note")

    return response.json()

def test_update_note():
    """Test updating an existing note"""
    print("\n" + "="*60)
    print("TEST 3: Update existing note")
    print("="*60)

    test_url = "https://www.linkedin.com/in/test-profile/"
    updated_note = "Updated: Interviewed on 10/25. Very strong candidate. Recommend hire."

    response = requests.post(
        f"{BASE_URL}/notes",
        json={
            "linkedin_url": test_url,
            "note": updated_note
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Note updated successfully!")
    else:
        print("❌ Failed to update note")

    return response.json()

def test_clear_note():
    """Test clearing a note (setting to empty string)"""
    print("\n" + "="*60)
    print("TEST 4: Clear note")
    print("="*60)

    test_url = "https://www.linkedin.com/in/test-profile/"

    response = requests.post(
        f"{BASE_URL}/notes",
        json={
            "linkedin_url": test_url,
            "note": ""
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✅ Note cleared successfully!")
    else:
        print("❌ Failed to clear note")

    return response.json()

def test_nonexistent_candidate():
    """Test getting note for non-existent candidate"""
    print("\n" + "="*60)
    print("TEST 5: Get note for non-existent candidate")
    print("="*60)

    fake_url = "https://www.linkedin.com/in/nonexistent-user-12345/"

    from urllib.parse import quote
    encoded_url = quote(fake_url, safe='')

    response = requests.get(f"{BASE_URL}/notes/{encoded_url}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200 and response.json().get('note') is None:
        print("✅ Correctly returned null for non-existent candidate")
    else:
        print("⚠️  Unexpected response for non-existent candidate")

    return response.json()

def test_with_real_candidate():
    """Test with a real candidate from the database"""
    print("\n" + "="*60)
    print("TEST 6: Test with real candidate from database")
    print("="*60)

    # First, let's search for a candidate
    search_response = requests.post(
        f"{BASE_URL}/search-and-rank",
        json={
            "query": "Python developer",
            "connected_to": "all"
        }
    )

    if search_response.status_code == 200:
        results = search_response.json().get('results', [])
        if results:
            # Get the first candidate
            candidate = results[0]
            linkedin_url = candidate.get('linkedin_url')
            name = candidate.get('name')

            print(f"Found candidate: {name}")
            print(f"LinkedIn URL: {linkedin_url}")

            # Add a note
            note_text = f"HR Note: {name} looks like a strong match for the Python role. Schedule interview."

            add_response = requests.post(
                f"{BASE_URL}/notes",
                json={
                    "linkedin_url": linkedin_url,
                    "note": note_text
                }
            )

            print(f"\nAdd Note Status: {add_response.status_code}")
            print(f"Add Note Response: {json.dumps(add_response.json(), indent=2)}")

            # Get the note back
            from urllib.parse import quote
            encoded_url = quote(linkedin_url, safe='')
            get_response = requests.get(f"{BASE_URL}/notes/{encoded_url}")

            print(f"\nGet Note Status: {get_response.status_code}")
            print(f"Get Note Response: {json.dumps(get_response.json(), indent=2)}")

            if get_response.status_code == 200 and get_response.json().get('note') == note_text:
                print("\n✅ Successfully added and retrieved note for real candidate!")
            else:
                print("\n❌ Failed to verify note for real candidate")
        else:
            print("❌ No candidates found in search")
    else:
        print("❌ Search failed")

def main():
    """Run all tests"""
    print("🚀 Starting Notes API Tests")
    print("Make sure the backend is running on http://localhost:5000")
    print("="*60)

    try:
        # Check if backend is running
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Backend is not responding. Please start the backend first.")
            print("   Run: cd website/backend && python app.py")
            return

        print("✅ Backend is running")

        # Run basic tests
        test_add_note()
        test_get_note()
        test_update_note()
        test_clear_note()
        test_nonexistent_candidate()

        # Run test with real candidate
        test_with_real_candidate()

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Please start the backend first.")
        print("   Run: cd website/backend && python app.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
