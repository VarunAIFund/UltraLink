#!/usr/bin/env python3
"""
Apify LinkedIn Data Scraper

Uses Apify's LinkedIn scraper to get profile data from LinkedIn URLs
"""

import json
import os
import csv
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv('APIFY_KEY'))
input_file = "connections_data/jon_connections.csv"
name = input_file.split("/")[-1].replace("_connections.csv", "").replace("connections_data/", "")
csv_size = 0
# Check for existing results
existing_urls = set()
try:
    with open(f'results/{name}_connections.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
        for item in existing_data:
            existing_urls.add(item['linkedinUrl'])
except FileNotFoundError:
    pass

# Open and read the CSV file
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    linkedin_urls = []
    for row in reader:
        url = row['URL']
        if url not in existing_urls:
            linkedin_urls.append(url)

csv_size = len(linkedin_urls)
batch_size = 200
num_batches = (csv_size + batch_size - 1) // batch_size  # Ceiling division

print(f"Total URLs to process: {csv_size}")
print(f"Batch size: {batch_size}")
print(f"Number of batches: {num_batches}")

# Process URLs in batches
all_results = []
current_time = datetime.now().isoformat()

for batch_num in range(num_batches):
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, csv_size)
    batch_urls = linkedin_urls[start_idx:end_idx]
    
    print(f"\nProcessing batch {batch_num + 1}/{num_batches} ({len(batch_urls)} URLs)")
    
    # Prepare the Actor input
    run_input = { 
        "profileUrls": batch_urls
    }
    
    # Run the Actor and wait for it to finish
    if len(batch_urls) > 0:
        run = client.actor("2SyF0bVxmgGr8IVCZ").call(run_input=run_input)
        
        # Fetch and print Actor results from the run's dataset
        batch_results = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # Add timestamp to each entry
            if 'connected_to' not in item:
                item['connected_to'] = []
            item['connected_to'].append(name)
            item['connected_to'] = list(set(item['connected_to']))
            item['scraped_at'] = current_time
            batch_results.append(item)
        
        all_results.extend(batch_results)
        print(f"Batch {batch_num + 1} completed: {len(batch_results)} profiles scraped")

results = all_results

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