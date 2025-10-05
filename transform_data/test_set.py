#!/usr/bin/env python3
"""
Create Test Dataset

Extracts a small subset of profiles from larger JSON files for development and testing.
Creates test.json with the first profile for quick AI transformation testing.
"""

import json

with open('../data/output/batch_001_with_parsed.json', 'r') as f:
    data = json.load(f)

first_10 = data[:1]

with open('test.json', 'w') as f:
    json.dump(first_10, f)