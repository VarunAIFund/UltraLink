#!/usr/bin/env python3
"""
Apify LinkedIn Data Scraper

Uses Apify's LinkedIn scraper to get profile data from LinkedIn URLs
"""

import json
import os
import csv
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv('APIFY_KEY'))
input_file = "connections_data/linda_connections.csv"
name = input_file.split("/")[-1].replace("_connections.csv", "").replace("connections_data/", "")
# Check for existing results
existing_urls = set()
try:
    with open(f'results/{name}_connections.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
        for item in existing_data:
            existing_urls.add(item['linkedinUrl'])
except FileNotFoundError:
    pass

print(existing_urls)

# Open and read the CSV file
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    linkedin_urls = []
    for row in reader:
        url = row['URL']
        if url not in existing_urls:
            linkedin_urls.append(url)

# Prepare the Actor input
run_input = { 
    "profileUrls": linkedin_urls[:2]
}
print(f"linkedin_urls: {linkedin_urls[0]}")
print(run_input)
# Run the Actor and wait for it to finish
if len(linkedin_urls) > 0:
    run = client.actor("2SyF0bVxmgGr8IVCZ").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
results = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    results.append(item)

# Save results to JSON file
os.makedirs('results', exist_ok=True)

# Load existing results and append new ones
try:
    with open(f'results/{name}_connections.json', 'r', encoding='utf-8') as f:
        existing_results = json.load(f)
except FileNotFoundError:
    existing_results = []

# Combine existing and new results
combined_results = existing_results + results

with open(f'results/{name}_connections.json', 'w', encoding='utf-8') as f:
    json.dump(combined_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Scraped {len(results)} profiles")
print(f"📄 Results saved to: apify_results.json")