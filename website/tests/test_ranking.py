"""
Test script for ranking.py - Loads test_search.json and ranks candidates
"""
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ranking import rank_candidates

# Load search results from test_search.json
input_path = os.path.join(os.path.dirname(__file__), 'output', 'test_search.json')
with open(input_path, 'r') as f:
    search_data = json.load(f)

query = "CEO in healthcare company with startup experience"
candidates = search_data.get('results', [])

print(f"Loaded {len(candidates)} candidates from test_search.json")
print(f"Query: {query}")
print(f"Ranking candidates using GPT-4o...\n")

# Rank candidates
ranked_results = rank_candidates(query, candidates)

# Prepare output - only keep essential fields
simplified_results = []
for candidate in ranked_results:
    simplified_results.append({
        'name': candidate.get('name'),
        'linkedin_url': candidate.get('linkedin_url'),
        'relevance_score': candidate.get('relevance_score'),
        'fit_description': candidate.get('fit_description')
    })

output_data = {
    'query': query,
    'original_sql': search_data.get('sql', ''),
    'total_candidates': len(candidates),
    'ranked_candidates': simplified_results
}

# Write to file in tests directory
output_path = os.path.join(os.path.dirname(__file__), 'output', 'test_ranking.json')
with open(output_path, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"✅ Results written to {output_path}")
print(f"Total ranked: {len(ranked_results)}")
