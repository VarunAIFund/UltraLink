"""
Test script for search.py
"""
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from search import execute_search

query = "CEO in healthcare comapny with startup experience"
result = execute_search(query)

# Write to file in tests directory
output_path = os.path.join(os.path.dirname(__file__), 'test_results.json')
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f"Results written to {output_path}")
print(f"SQL: {result['sql']}")
print(f"Total: {result['total']}")
