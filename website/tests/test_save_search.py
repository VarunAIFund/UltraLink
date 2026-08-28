"""
Test saving and retrieving search sessions from database.

Search sessions store only lightweight candidate references (linkedin_url +
search-specific metadata). Full candidate objects are reconstructed on read by
joining the candidates table, so these tests use real linkedin_urls.
"""
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from save_search import (
    save_search_session,
    get_search_session,
    slim_results,
    get_pooled_connection,
)

test_query = "Find Python developers in San Francisco"
test_connected_to = "all"
test_sql = "SELECT * FROM candidates WHERE skills @> ARRAY['Python'] LIMIT 100"


def _sample_candidates(n=2):
    """Pull a few real candidates to build a realistic search result payload."""
    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT linkedin_url, name FROM candidates WHERE name IS NOT NULL LIMIT %s",
            (n,),
        )
        return cursor.fetchall()


def test_slim_results_strips_profile_data():
    """slim_results should keep only references + search metadata."""
    print("\n[TEST] Testing slim_results()...")
    fat = [{
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "name": "John Doe",
        "headline": "Senior Python Developer",
        "skills": ["Python", "Django"],
        "experiences": [{"org": "Acme", "title": "Engineer"}],
        "education": [{"school": "MIT"}],
        "match": "strong",
        "relevance_score": 95,
        "score": 95,
        "fit_description": "Strong Python background",
    }]
    slim = slim_results(fat)
    assert set(slim[0].keys()) <= {
        "linkedin_url", "match", "relevance_score", "score",
        "stage_1_confidence", "fit_description", "ranking_rationale",
    }, f"slim result leaked profile fields: {slim[0].keys()}"
    assert "experiences" not in slim[0]
    assert slim[0]["fit_description"] == "Strong Python background"
    print("[TEST] slim_results() OK")
    return True


def test_save_and_retrieve():
    """Round-trip a search session and confirm hydration rebuilds full objects."""
    print("\n[TEST] Testing save_search_session / get_search_session...")

    sample = _sample_candidates(2)
    assert len(sample) == 2, "need at least 2 candidates in the database to test"

    test_results = [
        {
            "linkedin_url": sample[0][0],
            "match": "strong",
            "relevance_score": 95,
            "score": 95,
            "fit_description": "Experienced Python developer",
        },
        {
            "linkedin_url": sample[1][0],
            "match": "partial",
            "relevance_score": 70,
            "score": 70,
            "fit_description": "Adjacent experience",
        },
    ]

    search_id = save_search_session(test_query, test_connected_to, test_sql, test_results)
    print(f"[TEST] Saved search with ID: {search_id}")

    retrieved = get_search_session(search_id)
    assert retrieved, "failed to retrieve search session"
    assert retrieved['id'] == search_id
    assert retrieved['query'] == test_query
    assert retrieved['sql'] == test_sql
    assert retrieved['total'] == len(test_results)
    assert len(retrieved['results']) == len(test_results), "results count mismatch after hydration"

    first = retrieved['results'][0]
    # search metadata preserved
    assert first['linkedin_url'] == sample[0][0]
    assert first['match'] == "strong"
    assert first['relevance_score'] == 95
    assert first['fit_description'] == "Experienced Python developer"
    # profile data reconstructed from the candidates table
    assert first['name'] == sample[0][1], "hydration did not restore candidate name"
    assert 'experiences' in first, "hydration did not restore candidate experiences"

    print("[TEST] All assertions passed!")
    print(f"  First result: {first['name']} ({first['match']}, score {first['relevance_score']})")
    return True


def test_raw_storage_is_slim():
    """The row physically stored in Postgres must not contain profile data."""
    print("\n[TEST] Verifying stored payload is slim...")
    sample = _sample_candidates(1)
    results = [{
        "linkedin_url": sample[0][0],
        "match": "strong",
        "relevance_score": 88,
        "score": 88,
        "fit_description": "x" * 50,
    }]
    search_id = save_search_session("slim check", "all", "SELECT 1", results)

    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT results FROM search_sessions WHERE id = %s", (search_id,))
        stored = cursor.fetchone()[0]

    assert isinstance(stored, list) and len(stored) == 1
    assert "name" not in stored[0] and "experiences" not in stored[0], \
        f"stored payload still contains profile data: {stored[0].keys()}"
    print("[TEST] Stored payload is slim OK")
    return True


def test_nonexistent_search():
    print("\n[TEST] Testing retrieval of non-existent search...")
    result = get_search_session("00000000-0000-0000-0000-000000000000")
    assert result is None, "should return None for non-existent search"
    print("[TEST] Correctly returned None")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Search Session Save/Retrieve")
    print("=" * 60)

    try:
        results = [
            test_slim_results_strips_profile_data(),
            test_save_and_retrieve(),
            test_raw_storage_is_slim(),
            test_nonexistent_search(),
        ]
        print("\n" + "=" * 60)
        print("✓ All tests passed!" if all(results) else "✗ Some tests failed")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
