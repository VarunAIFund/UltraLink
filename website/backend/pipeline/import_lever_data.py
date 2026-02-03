#!/usr/bin/env python3
"""
Import Lever opportunities from JSON file to Supabase table.
This makes the data accessible from Railway without needing the local file.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'transform_data'))
from supabase_config import get_supabase_client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

supabase = get_supabase_client()

def normalize_linkedin_url(url):
    """Normalize LinkedIn URL for consistent matching"""
    if not url:
        return ""
    url = url.strip().rstrip('/')
    url = url.replace('https://', '').replace('http://', '')
    url = url.replace('www.', '')
    if not url.startswith('linkedin.com'):
        url = 'linkedin.com/' + url.lstrip('/')
    return url.lower()

def import_lever_data():
    """Import lever opportunities from JSON to Supabase"""
    json_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'transform_data', 
        'lever', 
        'linkedin_mapping_with_hired_status.json'
    )
    
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return
    
    print(f"📂 Loading Lever data from JSON...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} LinkedIn profiles with Lever opportunities")
    
    # Prepare batch insert with larger batches for speed
    batch_size = 500  # Increased from 100 to 500
    records = []
    total_inserted = 0
    
    print(f"📊 Processing {len(data)} records in batches of {batch_size}...")
    
    for i, (linkedin_url, opportunities) in enumerate(data.items(), 1):
        normalized_url = normalize_linkedin_url(linkedin_url)
        
        records.append({
            'linkedin_url': normalized_url,
            'opportunities': opportunities  # Already in correct format: [{url, hired}, ...]
        })
        
        # Insert in batches
        if len(records) >= batch_size:
            try:
                supabase.table('lever_candidates').upsert(records).execute()
                total_inserted += len(records)
                progress = (i / len(data)) * 100
                print(f"✅ Inserted batch (total: {total_inserted:,} / {len(data):,} = {progress:.1f}%)")
                records = []
            except Exception as e:
                print(f"❌ Error inserting batch: {e}")
                records = []
    
    # Insert remaining records
    if records:
        try:
            supabase.table('lever_candidates').upsert(records).execute()
            total_inserted += len(records)
            print(f"✅ Inserted final batch (total: {total_inserted:,} records)")
        except Exception as e:
            print(f"❌ Error inserting final batch: {e}")
    
    # Verify count
    try:
        count_response = supabase.table('lever_candidates').select('linkedin_url', count='exact').execute()
        total = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
        print(f"\n🎉 Import complete! Total records in table: {total}")
    except Exception as e:
        print(f"⚠️  Could not verify count: {e}")

if __name__ == "__main__":
    print("🚀 Starting Lever data import to Supabase...")
    import_lever_data()
    print("\n✅ Done!")
