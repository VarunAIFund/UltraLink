#!/usr/bin/env python3
"""
Apify LinkedIn Data Scraper

Uses Apify's LinkedIn scraper to get profile data from LinkedIn URLs
"""

import json
import os
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv('APIFY_KEY'))

# Prepare the Actor input
run_input = { 
    "profileUrls": [
        "https://www.linkedin.com/in/drodio/",
        "https://www.linkedin.com/in/andrewyng/"
    ] 
}

# Run the Actor and wait for it to finish
run = client.actor("2SyF0bVxmgGr8IVCZ").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
results = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    results.append(item)
    print(item)

# Save results to JSON file
with open('apify_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Scraped {len(results)} profiles")
print(f"📄 Results saved to: apify_results.json")