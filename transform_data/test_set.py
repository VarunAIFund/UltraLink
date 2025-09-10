import json

with open('../data/output/batch_001_with_parsed.json', 'r') as f:
    data = json.load(f)

first_10 = data[:1]

with open('test.json', 'w') as f:
    json.dump(first_10, f)