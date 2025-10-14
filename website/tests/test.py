"""
Test script for search.py
"""
import json
from search import execute_search

query = "CEO in healthcare comapny with startup experience"
result = execute_search(query)

# Write to file
with open('test_results.json', 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f"Results written to test_results.json")
print(f"SQL: {result['sql']}")
print(f"Total: {result['total']}")
