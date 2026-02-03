#!/usr/bin/env python3
"""
Apify LinkedIn Profile Scraper

Main LinkedIn profile scraping engine using Apify API with intelligent batch processing.
Processes CSV connection files, handles duplicates, tracks connection sources, and saves incrementally.
"""

import json
import os
import csv
import argparse
import contextlib
import io
import sys
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

# Add parent directory to path to import transform_data.supabase_config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform_data.supabase_config import get_supabase_client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Apify LinkedIn Profile Scraper')
parser.add_argument('--auto', '--all', action='store_true',
                   help='Process all batches without prompting (for automated pipelines)')
args = parser.parse_args()

# Initialize the ApifyClient with your API token
client = ApifyClient(os.getenv('APIFY_KEY'))
# Initialize Supabase client
supabase = get_supabase_client()

input_file = "connections_data/test_connections.csv"
name = input_file.split("/")[-1].replace("_connections.csv", "").replace("connections_data/", "")
csv_size = 0

# Check for existing results in the raw_profiles table
existing_urls = set()
existing_profiles = {}

print("Checking existing profiles in database...")
try:
    # Fetch all existing LinkedIn URLs from raw_profiles
    # Using pagination to handle large datasets
    page = 0
    page_size = 1000
    while True:
        result = supabase.table('raw_profiles').select('linkedin_url, connected_to').range(page * page_size, (page + 1) * page_size - 1).execute()
        if not result.data:
            break
            
        for item in result.data:
            linkedin_url = item['linkedin_url']
            existing_urls.add(linkedin_url)
            existing_profiles[linkedin_url] = item
            
        page += 1
        print(f"Loaded {len(existing_urls)} existing profiles...", end='\r')
        
    print(f"\nLoaded {len(existing_urls)} total existing profiles from database")
    
except Exception as e:
    print(f"Error checking existing profiles: {e}")
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
            connected_to = existing_profile.get('connected_to') or []
            if name not in connected_to:
                urls_to_update.append(url)  # Existing profile needs connection update

# Update existing profiles with new connection
if urls_to_update:
    print(f"Updating connection info for {len(urls_to_update)} existing profiles...")
    
    # Process updates in batches
    update_batch_size = 100
    for i in range(0, len(urls_to_update), update_batch_size):
        batch = urls_to_update[i:i+update_batch_size]
        
        for url in batch:
            current_connected_to = existing_profiles[url].get('connected_to') or []
            if name not in current_connected_to:
                current_connected_to.append(name)
                
            try:
                supabase.table('raw_profiles').update({
                    'connected_to': current_connected_to
                }).eq('linkedin_url', url).execute()
            except Exception as e:
                print(f"Error updating profile {url}: {e}")
        
        print(f"Updated {min(i + update_batch_size, len(urls_to_update))}/{len(urls_to_update)} profiles")

    print(f"💾 Saved {len(urls_to_update)} connection updates immediately")

csv_size = len(linkedin_urls)
batch_size = 100
num_batches = (csv_size + batch_size - 1) // batch_size  # Ceiling division

print(f"Total URLs to scrape: {csv_size}")
print(f"URLs to update connections: {len(urls_to_update)}")
print(f"Batch size: {batch_size}")
print(f"Total batches available: {num_batches}")

if urls_to_update:
    print(f"Updated {len(urls_to_update)} existing profiles with '{name}' connection")

# Determine how many batches to process
if csv_size > 0:
    if args.auto:
        # Auto mode: process all batches without prompting
        batches_to_process = num_batches
        print(f"\n🤖 Auto mode: Processing all {batches_to_process} batches")
    else:
        # Interactive mode: ask user
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
        # Suppress Apify output
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
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
        
        # Save progress incrementally after each batch to Database
        if batch_results:
            print(f"Saving batch {batch_num + 1} to database...")
            
            for item in batch_results:
                try:
                    # Prepare data for Supabase
                    profile_data = {
                        'linkedin_url': item.get('linkedinUrl'),
                        'full_name': item.get('fullName'),
                        'headline': item.get('headline'),
                        'location': item.get('addressWithCountry'),
                        'phone': item.get('mobileNumber'),
                        'email': item.get('email'),
                        'profile_pic': item.get('profilePic'),
                        'profile_pic_high_quality': item.get('profilePicHighQuality'),
                        'connections': item.get('connections', 0),  # Fixed: was connectionsCount
                        'followers': item.get('followers', 0),      # Fixed: was followersCount
                        'connected_to': item.get('connected_to', []),
                        'experiences': item.get('experiences', []),
                        'educations': item.get('educations', []),
                        'scraped_at': item.get('scraped_at'),
                        'transformed': False
                    }
                    
                    # Upsert to Supabase
                    supabase.table('raw_profiles').upsert(profile_data).execute()
                except Exception as e:
                    print(f"Error saving profile {item.get('linkedinUrl')}: {e}")
            
            print(f"💾 Saved batch {batch_num + 1} progress ({len(batch_results)} profiles) to raw_profiles table")

results = all_results

# Final summary
print(f"\n🎉 PROCESSING COMPLETE")
print(f"✅ Scraped {len(results)} new profiles")
print(f"📄 Updated {len(urls_to_update)} existing connections")
print(f"📄 All results saved incrementally to raw_profiles table")

# Show remaining work if applicable
if batches_to_process < num_batches:
    remaining_batches = num_batches - batches_to_process
    remaining_urls = csv_size - len(results)
    print(f"\n📋 REMAINING WORK:")
    print(f"   - {remaining_batches} batches remaining ({remaining_urls} URLs)")
    print(f"   - Run the script again to continue processing")