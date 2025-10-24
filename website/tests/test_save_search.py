"""
Test saving and retrieving search sessions from database
"""
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from save_search import save_search_session, get_search_session

# Test data
test_query = "Find Python developers in San Francisco"
test_connected_to = "all"
test_sql = "SELECT * FROM candidates WHERE skills @> ARRAY['Python'] AND location ILIKE '%San Francisco%' LIMIT 100"
test_results = [
    {
        "name": "John Doe",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "headline": "Senior Python Developer",
        "location": "San Francisco, CA, USA",
        "seniority": "Senior",
        "skills": ["Python", "Django", "PostgreSQL"],
        "relevance_score": 95,
        "fit_description": "Experienced Python developer with strong Django background",
        "ranking_insight": "High relevance due to Python expertise and SF location"
    },
    {
        "name": "Jane Smith",
        "linkedin_url": "https://linkedin.com/in/janesmith",
        "headline": "Python Engineer",
        "location": "San Francisco, CA, USA",
        "seniority": "Mid",
        "skills": ["Python", "Flask", "Docker"],
        "relevance_score": 88,
        "fit_description": "Mid-level Python engineer with modern DevOps skills",
        "ranking_insight": "Good match with Python and containerization experience"
    }
]

def test_save_and_retrieve():
    """Test saving and retrieving a search session"""
    print("[TEST] Testing save_search_session...")

    # Save search
    search_id = save_search_session(test_query, test_connected_to, test_sql, test_results)
    print(f"[TEST] Saved search with ID: {search_id}")

    # Retrieve search
    print(f"[TEST] Retrieving search with ID: {search_id}")
    retrieved = get_search_session(search_id)

    if not retrieved:
        print("[ERROR] Failed to retrieve search session")
        return False

    # Verify data
    print("[TEST] Verifying retrieved data...")
    assert retrieved['id'] == search_id, "ID mismatch"
    assert retrieved['query'] == test_query, "Query mismatch"
    assert retrieved['connected_to'] == test_connected_to, "Connected_to mismatch"
    assert retrieved['sql'] == test_sql, "SQL mismatch"
    assert retrieved['total'] == len(test_results), "Total mismatch"
    assert len(retrieved['results']) == len(test_results), "Results count mismatch"
    assert retrieved['results'][0]['name'] == test_results[0]['name'], "First result name mismatch"

    print("[TEST] All assertions passed!")
    print(f"\n[TEST] Retrieved search session:")
    print(f"  ID: {retrieved['id']}")
    print(f"  Query: {retrieved['query']}")
    print(f"  Connected To: {retrieved['connected_to']}")
    print(f"  SQL: {retrieved['sql'][:100]}...")
    print(f"  Total Results: {retrieved['total']}")
    print(f"  Created At: {retrieved['created_at']}")
    print(f"\n[TEST] First result:")
    print(f"  Name: {retrieved['results'][0]['name']}")
    print(f"  Relevance Score: {retrieved['results'][0]['relevance_score']}")
    print(f"  Fit: {retrieved['results'][0]['fit_description']}")

    return True

def test_nonexistent_search():
    """Test retrieving a non-existent search"""
    print("\n[TEST] Testing retrieval of non-existent search...")
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    result = get_search_session(fake_uuid)

    if result is None:
        print("[TEST] Correctly returned None for non-existent search")
        return True
    else:
        print("[ERROR] Should have returned None for non-existent search")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Search Session Save/Retrieve")
    print("=" * 60)

    try:
        # Test 1: Save and retrieve
        success1 = test_save_and_retrieve()

        # Test 2: Non-existent search
        success2 = test_nonexistent_search()

        if success1 and success2:
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ Some tests failed")
            print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
