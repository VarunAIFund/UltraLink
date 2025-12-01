#!/usr/bin/env python3
"""
Apify LinkedIn Company Scraper

Scrapes LinkedIn company data using Apify's company scraper actor
Based on JavaScript template but adapted for Python
"""

import json
import os
import argparse
import contextlib
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from apify_client import ApifyClient
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Thread-safe lock for file operations
file_lock = threading.Lock()

# Get script directory and parent directory for proper path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)  # get_data/

# Initialize the ApifyClient with API token
client = ApifyClient(os.getenv('APIFY_KEY'))

def load_company_urls(input_file=None):
    """Load company URLs from JSON file"""

    # Use default path if not provided
    if input_file is None:
        input_file = os.path.join(PARENT_DIR, "company_urls.json")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        company_urls = data.get('company_urls', [])
        print(f"📊 Loaded {len(company_urls)} company URLs from {input_file}")
        return company_urls
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        print("💡 Run extract_company_urls.py first to generate company URLs")
        return []

def check_existing_companies():
    """Check for existing company results to avoid duplicates"""

    # Construct path relative to script location
    companies_file = os.path.join(PARENT_DIR, "results", "companies.json")

    existing_input_urls = set()
    try:
        with open(companies_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            for item in existing_data:
                # Check the input_linkedin_url field to see what was already scraped
                input_url = item.get('input_linkedin_url')
                if input_url and input_url != "unknown":
                    existing_input_urls.add(input_url)
        
        print(f"📋 Found {len(existing_input_urls)} existing companies to skip")
        
    except FileNotFoundError:
        existing_data = []
    
    return existing_input_urls, existing_data

def process_batch(batch_num, batch_urls, total_batches):
    """Process a single batch of company URLs

    Args:
        batch_num: Current batch number (0-indexed)
        batch_urls: List of LinkedIn company URLs to scrape
        total_batches: Total number of batches being processed

    Returns:
        List of scraped company data
    """
    try:
        print(f"[Worker {batch_num + 1}] Starting batch {batch_num + 1}/{total_batches} ({len(batch_urls)} companies)")

        # Prepare the Actor input
        run_input = {
            "profileUrls": batch_urls
        }

        # Run the Actor and wait for it to finish
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            run = client.actor("AjfNXEI9qTA2IdaAX").call(run_input=run_input)

        # Fetch Actor results from the run's dataset
        batch_results = []
        current_time = datetime.now().isoformat()
        results_list = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        for i, item in enumerate(results_list):
            # Reorder fields to put input_linkedin_url right after url
            ordered_item = {}

            # Add url first if it exists
            if 'url' in item:
                ordered_item['url'] = item['url']

            # Add input LinkedIn URL right after url
            if i < len(batch_urls):
                ordered_item['input_linkedin_url'] = batch_urls[i]
            else:
                # Fallback if results don't match input count exactly
                ordered_item['input_linkedin_url'] = batch_urls[0] if batch_urls else "unknown"

            # Add all other fields in original order
            for key, value in item.items():
                if key != 'url':  # Skip url since we already added it
                    ordered_item[key] = value

            # Add timestamp to each entry
            ordered_item['scraped_at'] = current_time
            batch_results.append(ordered_item)

        print(f"[Worker {batch_num + 1}] ✅ Batch {batch_num + 1}/{total_batches} completed: {len(batch_results)} companies scraped")

        # Save progress incrementally (thread-safe)
        if batch_results:
            with file_lock:
                # Construct paths relative to script location
                results_dir = os.path.join(PARENT_DIR, "results")
                companies_file = os.path.join(results_dir, "companies.json")

                # Load current companies file
                try:
                    with open(companies_file, 'r', encoding='utf-8') as f:
                        current_companies = json.load(f)
                except FileNotFoundError:
                    current_companies = []

                # Append new batch results
                current_companies.extend(batch_results)

                # Ensure results directory exists
                os.makedirs(results_dir, exist_ok=True)

                # Save updated file
                with open(companies_file, 'w', encoding='utf-8') as f:
                    json.dump(current_companies, f, indent=2, ensure_ascii=False)

                print(f"[Worker {batch_num + 1}] 💾 Saved batch {batch_num + 1} progress ({len(current_companies)} total companies)")

        return batch_results

    except Exception as e:
        print(f"[Worker {batch_num + 1}] ❌ Error processing batch {batch_num + 1}: {str(e)}")
        return []

def scrape_companies(auto_mode=False, max_workers=20):
    """Main company scraping function

    Args:
        auto_mode: If True, process all batches without prompting (default: False)
        max_workers: Number of concurrent workers (default: 20, max: 32)
    """
    # Limit workers to max 32 (Apify concurrent run limit)
    max_workers = min(max_workers, 32)

    print("🏢 LinkedIn Company Scraper")
    print("=" * 50)
    
    # Load company URLs
    company_urls = load_company_urls()
    if not company_urls:
        return
    
    # Check for existing results
    existing_input_urls, existing_data = check_existing_companies()
    print(existing_input_urls)
    
    # Filter out already scraped companies
    new_urls = [url for url in company_urls if url not in existing_input_urls]
    
    print(f"Total company URLs: {len(company_urls)}")
    print(f"Already scraped: {len(existing_input_urls)}")
    print(f"New URLs to scrape: {len(new_urls)}")

    if not new_urls:
        print("✅ All companies already scraped!")
        return

    # Batch processing setup
    batch_size = 100  # Smaller batches for company data
    total_batches = (len(new_urls) + batch_size - 1) // batch_size

    print(f"Batch size: {batch_size}")
    print(f"Total batches available: {total_batches}")
    print(f"Concurrent workers: {max_workers}")
    
    # Determine how many batches to process
    if len(new_urls) > 0:
        if auto_mode:
            # Auto mode: process all batches without prompting
            batches_to_process = total_batches
            print(f"\n🤖 Auto mode: Processing all {batches_to_process} batches")
        else:
            # Interactive mode: ask user
            while True:
                try:
                    user_input = input(f"\nHow many batches do you want to scrape? (1-{total_batches}, or 'all'): ").strip().lower()

                    if user_input == 'all':
                        batches_to_process = total_batches
                        break
                    else:
                        batches_to_process = int(user_input)
                        if 1 <= batches_to_process <= total_batches:
                            break
                        else:
                            print(f"Please enter a number between 1 and {total_batches}, or 'all'")
                except ValueError:
                    print("Please enter a valid number or 'all'")

        print(f"\n🚀 Processing {batches_to_process} batches using {max_workers} concurrent workers")
        remaining_urls = len(new_urls) - (batches_to_process * batch_size)
        if remaining_urls > 0:
            print(f"📋 {remaining_urls} companies will remain for future processing")
    else:
        batches_to_process = 0

    # Process companies in concurrent batches
    all_results = []

    if batches_to_process > 0:
        print(f"\n{'='*60}")
        print(f"🚀 STARTING CONCURRENT SCRAPING")
        print(f"{'='*60}")

        # Create batch tasks
        batch_tasks = []
        for batch_num in range(batches_to_process):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(new_urls))
            batch_urls = new_urls[start_idx:end_idx]
            batch_tasks.append((batch_num, batch_urls, batches_to_process))

        # Execute batches concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch tasks
            future_to_batch = {
                executor.submit(process_batch, batch_num, batch_urls, total_batches): batch_num
                for batch_num, batch_urls, total_batches in batch_tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                except Exception as e:
                    print(f"[Main] ❌ Exception in batch {batch_num + 1}: {str(e)}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 COMPANY SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Scraped {len(all_results)} new companies")

    # Get final count from file
    companies_file = os.path.join(PARENT_DIR, "results", "companies.json")
    try:
        with open(companies_file, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        final_count = len(final_data)
    except FileNotFoundError:
        final_count = 0

    print(f"📄 Total companies in companies.json: {final_count}")
    print(f"📄 All results saved to: {companies_file}")
    
    # Show remaining work if applicable
    if batches_to_process < total_batches:
        remaining_batches = total_batches - batches_to_process
        remaining_companies = len(new_urls) - len(all_results)
        print(f"\n📋 REMAINING WORK:")
        print(f"   - {remaining_batches} batches remaining ({remaining_companies} companies)")
        print(f"   - Run the script again to continue processing")

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Apify LinkedIn Company Scraper')
    parser.add_argument('--auto', '--all', action='store_true',
                       help='Process all batches without prompting (for automated pipelines)')
    parser.add_argument('--workers', type=int, default=20,
                       help='Number of concurrent workers (default: 20, max: 32)')
    args = parser.parse_args()

    scrape_companies(auto_mode=args.auto, max_workers=args.workers)

if __name__ == "__main__":
    main()