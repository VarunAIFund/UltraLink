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
# Check for existing results in the master connections file
existing_urls = set()
existing_profiles = {}
try:
    with open('results/connections.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
        for item in existing_data:
            linkedin_url = item['linkedinUrl']
            existing_urls.add(linkedin_url)
            existing_profiles[linkedin_url] = item
except FileNotFoundError:
    existing_data = []

# Open and read the CSV file
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    linkedin_urls = []
    urls_to_update = []  # URLs that exist but need connection update
    
    for row in reader:
        url = row['URL']
        if url not in existing_urls:
            linkedin_urls.append(url)  # New URLs to scrape
        else:
            # Check if this connection source is already in the profile
            existing_profile = existing_profiles[url]
            if name not in existing_profile.get('connected_to', []):
                urls_to_update.append(url)  # Existing profile needs connection update

# Update existing profiles with new connection
for url in urls_to_update:
    existing_profiles[url]['connected_to'].append(name)
    existing_profiles[url]['connected_to'] = list(set(existing_profiles[url]['connected_to']))

csv_size = len(linkedin_urls)
batch_size = 100
num_batches = (csv_size + batch_size - 1) // batch_size  # Ceiling division

print(f"Total URLs to scrape: {csv_size}")
print(f"URLs to update connections: {len(urls_to_update)}")
print(f"Batch size: {batch_size}")
print(f"Total batches available: {num_batches}")

if urls_to_update:
    print(f"Updated {len(urls_to_update)} existing profiles with '{name}' connection")

# Ask user how many batches to process
if csv_size > 0:
    while True:
        try:
            user_input = input(f"\nHow many batches do you want to scrape? (1-{num_batches}, or 'all'): ").strip().lower()
            
            if user_input == 'all':
                batches_to_process = num_batches
                break
            else:
                batches_to_process = int(user_input)
                if 1 <= batches_to_process <= num_batches:
                    break
                else:
                    print(f"Please enter a number between 1 and {num_batches}, or 'all'")
        except ValueError:
            print("Please enter a valid number or 'all'")
    
    print(f"\n🚀 Processing {batches_to_process} out of {num_batches} available batches")
    remaining_urls = csv_size - (batches_to_process * batch_size)
    if remaining_urls > 0:
        print(f"📋 {remaining_urls} URLs will remain for future processing")
else:
    batches_to_process = 0
    print("\n🎉 No new URLs to scrape!")

# Process URLs in batches
all_results = []
current_time = datetime.now().isoformat()

for batch_num in range(batches_to_process):
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, csv_size)
    batch_urls = linkedin_urls[start_idx:end_idx]
    
    print(f"\nProcessing batch {batch_num + 1}/{batches_to_process} requested ({len(batch_urls)} URLs)")
    
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
        print(f"✅ Batch {batch_num + 1}/{batches_to_process} completed: {len(batch_results)} profiles scraped")

results = all_results

# Save results to the master connections file
os.makedirs('results', exist_ok=True)

# Combine all profiles: existing + updated + newly scraped
all_profiles = []

# Add updated existing profiles
for profile in existing_data:
    linkedin_url = profile['linkedinUrl']
    if linkedin_url in existing_profiles:
        # Use the updated version (with new connections)
        all_profiles.append(existing_profiles[linkedin_url])
    else:
        # Keep original version
        all_profiles.append(profile)

# Add newly scraped profiles
all_profiles.extend(results)

# Save to master connections file
with open('results/connections.json', 'w', encoding='utf-8') as f:
    json.dump(all_profiles, f, indent=2, ensure_ascii=False)

print(f"\n🎉 PROCESSING COMPLETE")
print(f"✅ Scraped {len(results)} new profiles")
print(f"📄 Updated {len(urls_to_update)} existing connections")
print(f"📄 Total profiles in connections.json: {len(all_profiles)}")
print(f"📄 Results saved to: results/connections.json")

# Show remaining work if applicable
if batches_to_process < num_batches:
    remaining_batches = num_batches - batches_to_process
    remaining_urls = csv_size - len(results)
    print(f"\n📋 REMAINING WORK:")
    print(f"   - {remaining_batches} batches remaining ({remaining_urls} URLs)")
    print(f"   - Run the script again to continue processing")