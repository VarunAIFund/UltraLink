"""
Test ranking stage 1 classification
"""
import sys
import os
import json
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from search import execute_search
from ranking_stage_1 import classify_candidates

async def test_classification():
    """Test classification with CEO healthcare startup query"""
    query = "CEO at healthcare company with startup experience"

    print(f"Testing query: {query}")
    print("="*80)

    # Execute search
    print("\n1. Executing search...")
    search_result = execute_search(query, connected_to='all')
    print(f"   Found {len(search_result['results'])} candidates")
    print(f"   SQL: {search_result['sql'][:100]}...")

    # Classify candidates
    print("\n2. Classifying candidates...")
    classification_result = await classify_candidates(query, search_result['results'])

    strong_matches = classification_result['strong_matches']
    partial_matches = classification_result['partial_matches']

    print(f"   Strong matches: {len(strong_matches)}")
    print(f"   Partial matches: {len(partial_matches)}")

    # Save results with only linkedin_url, name, and fit_description
    strong_matches_clean = [
        {
            'linkedin_url': c.get('linkedin_url'),
            'name': c.get('name'),
            'fit_description': c.get('fit_description')
        }
        for c in strong_matches
    ]

    partial_matches_clean = [
        {
            'linkedin_url': c.get('linkedin_url'),
            'name': c.get('name'),
            'fit_description': c.get('fit_description')
        }
        for c in partial_matches
    ]

    output_file = os.path.join(os.path.dirname(__file__), 'output', 'classification_results.json')
    output_data = {
        'query': query,
        'sql': search_result['sql'],
        'total_candidates': len(search_result['results']),
        'strong_match_count': len(strong_matches),
        'partial_match_count': len(partial_matches),
        'strong_matches': strong_matches_clean,
        'partial_matches': partial_matches_clean
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n3. Results saved to: {output_file}")

    # Print sample strong matches
    if strong_matches:
        print("\n4. Sample strong matches:")
        for i, candidate in enumerate(strong_matches[:3], 1):
            print(f"\n   {i}. {candidate.get('name')}")
            print(f"      Headline: {candidate.get('headline')}")
            print(f"      Seniority: {candidate.get('seniority')}")
            print(f"      Location: {candidate.get('location')}")
            print(f"      Startup exp: {candidate.get('worked_at_startup')}")
            print(f"      Fit: {candidate.get('fit_description')}")

    # Print sample partial matches
    if partial_matches:
        print("\n5. Sample partial matches:")
        for i, candidate in enumerate(partial_matches[:3], 1):
            print(f"\n   {i}. {candidate.get('name')}")
            print(f"      Headline: {candidate.get('headline')}")
            print(f"      Seniority: {candidate.get('seniority')}")
            print(f"      Fit: {candidate.get('fit_description')}")

    print("\n" + "="*80)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_classification())
