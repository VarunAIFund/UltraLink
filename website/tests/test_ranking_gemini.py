"""
Test Gemini ranking with all candidates
"""
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from search import execute_search
from ranking_gemini import rank_candidates_gemini

def test_gemini_ranking():
    """Test Gemini ranking with CEO healthcare startup query"""
    query = "CEO at healthcare company with startup experience"

    print(f"Testing Gemini ranking with query: {query}")
    print("="*80)

    # Execute search
    print("\n1. Executing search...")
    search_result = execute_search(query, connected_to='all')
    print(f"   Found {len(search_result['results'])} candidates")
    print(f"   SQL: {search_result['sql'][:100]}...")

    # Rank with Gemini
    print("\n2. Ranking all candidates with Gemini...")
    ranked_candidates = rank_candidates_gemini(query, search_result['results'])

    print(f"   Ranked: {len(ranked_candidates)} candidates")

    # Save results with only essential fields
    ranked_clean = [
        {
            'linkedin_url': c.get('linkedin_url'),
            'name': c.get('name'),
            'relevance_score': c.get('relevance_score'),
            'fit_description': c.get('fit_description')
        }
        for c in ranked_candidates
    ]

    output_file = "gemini_ranking_results.json"
    output_data = {
        'query': query,
        'sql': search_result['sql'],
        'total_candidates': len(search_result['results']),
        'ranked_count': len(ranked_candidates),
        'ranked_candidates': ranked_clean
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n3. Results saved to: {output_file}")

    # Print top 5 candidates
    if ranked_candidates:
        print("\n4. Top 5 candidates:")
        for i, candidate in enumerate(ranked_candidates[:5], 1):
            print(f"\n   {i}. {candidate.get('name')} (Score: {candidate.get('relevance_score')})")
            print(f"      Headline: {candidate.get('headline')}")
            print(f"      Seniority: {candidate.get('seniority')}")
            print(f"      Location: {candidate.get('location')}")
            print(f"      Fit: {candidate.get('fit_description')}")

    print("\n" + "="*80)
    print("Gemini ranking test complete!")

if __name__ == "__main__":
    test_gemini_ranking()
