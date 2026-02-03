import os
import csv
import sys
import time
import json
import asyncio
import gc
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform.supabase_config import get_supabase_client
from transform.transform import process_batch_concurrent
from transform.upload_to_supabase import transform_profile_for_db

# Load env (now in website/.env)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Constants
BATCH_SIZE = 100
MAX_RETRIES = 3

class StreamProcessor:
    def __init__(self, job_id=None, connection_owner=None):
        self.job_id = job_id
        self.connection_owner = connection_owner
        self.supabase = get_supabase_client()
        self.apify_client = ApifyClient(os.getenv('APIFY_KEY'))
        self.logs = []

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.logs.append(log_entry)
        
        # Update logs in DB every 10 logs or important updates
        if self.job_id and (len(self.logs) % 10 == 0 or "Error" in message or "Completed" in message):
            self._update_job_logs()

    def _update_job_logs(self):
        try:
            current_logs = "\n".join(self.logs)
            self.supabase.table('upload_jobs').update({'logs': current_logs}).eq('id', self.job_id).execute()
        except Exception as e:
            print(f"Failed to update logs: {e}")

    def _ensure_receiver_exists(self):
        """
        Ensure the connection_owner exists in the receivers table.
        If not, add them automatically.
        """
        if not self.connection_owner:
            return
        
        try:
            # Check if receiver exists
            existing = self.supabase.table('receivers') \
                .select('username') \
                .eq('username', self.connection_owner) \
                .execute()
            
            if not existing.data:
                # Add new receiver
                display_name = self.connection_owner.title()  # Capitalize first letter
                email = f"{self.connection_owner}@example.com"  # Placeholder email
                
                self.supabase.table('receivers').insert({
                    'username': self.connection_owner,
                    'display_name': display_name,
                    'email': email
                }).execute()
                
                self.log(f"✅ Added new receiver to dropdown: {display_name}")
        except Exception as e:
            self.log(f"Warning: Could not add receiver to table: {e}")
    
    def _update_job_status(self, status, **kwargs):
        if not self.job_id:
            return
        
        data = {'status': status, **kwargs}
        if status == 'completed':
            data['completed_at'] = datetime.now().isoformat()
        elif status == 'processing' and not kwargs.get('started_at'):
            data['started_at'] = datetime.now().isoformat()
            
        try:
            self.supabase.table('upload_jobs').update(data).eq('id', self.job_id).execute()
        except Exception as e:
            self.log(f"Error updating job status: {e}")

    def parse_csv(self, file_path):
        self.log(f"Parsing CSV: {file_path}")
        linkedin_urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'URL' in row and row['URL']:
                        linkedin_urls.append(row['URL'])
                    elif 'linkedinUrl' in row and row['linkedinUrl']:
                        linkedin_urls.append(row['linkedinUrl'])
            
            self.log(f"Found {len(linkedin_urls)} URLs in CSV")
            if self.job_id:
                self.supabase.table('upload_jobs').update({'total_urls': len(linkedin_urls)}).eq('id', self.job_id).execute()
            
            return linkedin_urls
        except Exception as e:
            self.log(f"Error parsing CSV: {e}")
            raise

    def scrape_batch(self, urls):
        """Scrape a batch of URLs using Apify"""
        if not urls:
            return []
            
        run_input = {"profileUrls": urls}
        
        try:
            # Run Apify actor
            run = self.apify_client.actor("2SyF0bVxmgGr8IVCZ").call(run_input=run_input)
            
            # Fetch results
            results = []
            dataset = self.apify_client.dataset(run["defaultDatasetId"])
            
            for item in dataset.iterate_items():
                # Add metadata
                if self.connection_owner:
                    if 'connected_to' not in item:
                        item['connected_to'] = []
                    if self.connection_owner not in item['connected_to']:
                        item['connected_to'].append(self.connection_owner)
                
                item['scraped_at'] = datetime.now().isoformat()
                results.append(item)
                
            return results
        except Exception as e:
            self.log(f"Apify scraping error: {e}")
            return []

    def save_raw_profiles(self, profiles):
        """Save raw scraped profiles to Supabase"""
        if not profiles:
            return 0
            
        saved_count = 0
        for item in profiles:
            try:
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
                
                self.supabase.table('raw_profiles').upsert(profile_data).execute()
                saved_count += 1
            except Exception as e:
                self.log(f"Error saving raw profile {item.get('linkedinUrl')}: {e}")
        
        return saved_count

    async def run(self, csv_path):
        try:
            self._update_job_status('scraping', started_at=datetime.now().isoformat())
            
            # 0. Ensure connection owner is in receivers table (for dropdown)
            self._ensure_receiver_exists()
            
            # 1. Parse CSV
            urls = self.parse_csv(csv_path)
            
            # 2. Check for existing profiles to avoid re-scraping
            self.log("Checking for existing profiles in database...")
            existing_urls = set()
            existing_profiles = {}
            
            try:
                page = 0
                page_size = 1000
                while True:
                    response = self.supabase.table('raw_profiles') \
                        .select('linkedin_url, connected_to') \
                        .range(page * page_size, (page + 1) * page_size - 1) \
                        .execute()
                    
                    if not response.data:
                        break
                    
                    for item in response.data:
                        linkedin_url = item.get('linkedin_url')
                        if linkedin_url:
                            existing_urls.add(linkedin_url)
                            existing_profiles[linkedin_url] = item
                    
                    page += 1
                    
                self.log(f"Found {len(existing_urls)} existing profiles in database")
            except Exception as e:
                self.log(f"Error checking existing profiles: {e}")
            
            # Separate URLs into new vs existing
            urls_to_scrape = []
            urls_to_update = []  # URLs that exist but need connection update
            
            for url in urls:
                if url not in existing_urls:
                    urls_to_scrape.append(url)
                else:
                    # Check if this connection source is already in the profile
                    existing_profile = existing_profiles.get(url, {})
                    connected_to = existing_profile.get('connected_to') or []
                    if self.connection_owner and self.connection_owner not in connected_to:
                        urls_to_update.append(url)
            
            self.log(f"New URLs to scrape: {len(urls_to_scrape)}")
            self.log(f"Existing URLs to update connection: {len(urls_to_update)}")
            
            # Update existing profiles with new connection
            updated_count = 0
            if urls_to_update:
                self.log(f"Updating connection info for {len(urls_to_update)} existing profiles...")
                for url in urls_to_update:
                    try:
                        current_connected_to = existing_profiles[url].get('connected_to') or []
                        if self.connection_owner and self.connection_owner not in current_connected_to:
                            current_connected_to.append(self.connection_owner)
                            self.supabase.table('raw_profiles').update({
                                'connected_to': current_connected_to
                            }).eq('linkedin_url', url).execute()
                            updated_count += 1
                    except Exception as e:
                        self.log(f"Error updating profile {url}: {e}")
                
                self.log(f"Updated {updated_count} existing profiles")
            
            # 3. Scrape only NEW URLs in batches
            scraped_total = updated_count  # Start with updated count
            
            if not urls_to_scrape:
                self.log("No new URLs to scrape - all profiles already exist!")
                # Still update counter to show all were processed
                self.supabase.table('upload_jobs').update({'scraped_urls': scraped_total}).eq('id', self.job_id).execute()
            else:
                # Create chunks
                chunks = [urls_to_scrape[i:i + BATCH_SIZE] for i in range(0, len(urls_to_scrape), BATCH_SIZE)]
                
                for i, batch_urls in enumerate(chunks):
                    self.log(f"Scraping batch {i+1}/{len(chunks)} ({len(batch_urls)} URLs)")
                    self._update_job_status('scraping', current_step=f"Scraping batch {i+1}/{len(chunks)}")
                    
                    profiles = self.scrape_batch(batch_urls)
                    saved = self.save_raw_profiles(profiles)
                    scraped_total += saved
                    
                    self.supabase.table('upload_jobs').update({'scraped_urls': scraped_total}).eq('id', self.job_id).execute()
                    
                    # Free memory
                    del profiles
                    gc.collect()
            
            self.log(f"Scraping completed. Total processed: {scraped_total} (skipped {len(urls) - len(urls_to_scrape)} existing)")
            
            # 3. Transform
            self._update_job_status('transforming')
            transformed_total = 0
            
            # First, check how many profiles need transformation
            count_response = self.supabase.table('raw_profiles') \
                .select('linkedin_url', count='exact') \
                .eq('transformed', False) \
                .eq('transform_failed', False) \
                .execute()
            
            total_to_transform = count_response.count if hasattr(count_response, 'count') else 0
            self.log(f"Found {total_to_transform} profiles to transform")
            
            if total_to_transform == 0:
                self.log("No profiles to transform - all profiles already transformed or failed")
                # Set transformed count to total (all already done)
                job_data = self.supabase.table('upload_jobs').select('total_urls').eq('id', self.job_id).execute()
                total_urls = job_data.data[0]['total_urls'] if job_data.data else 0
                self.supabase.table('upload_jobs').update({'transformed_urls': total_urls}).eq('id', self.job_id).execute()
                self._update_job_status('completed')
                return
            
            # Fetch unprocessed from DB
            while True:
                response = self.supabase.table('raw_profiles') \
                    .select('*') \
                    .eq('transformed', False) \
                    .eq('transform_failed', False) \
                    .limit(BATCH_SIZE) \
                    .execute()
                
                batch = response.data
                if not batch:
                    self.log("No more batches to process")
                    break
                
                self.log(f"Transforming batch of {len(batch)} profiles...")
                
                try:
                    # Map for transform function - MUST match what extract_profile_data expects!
                    mapped_batch = []
                    for p in batch:
                        mapped_batch.append({
                            "linkedinUrl": p.get('linkedin_url'),
                            "fullName": p.get('full_name'),
                            "headline": p.get('headline'),
                            "addressWithCountry": p.get('location'),
                            "mobileNumber": p.get('phone', ''),
                            "email": p.get('email', ''),
                            "profilePic": p.get('profile_pic', ''),
                            "profilePicHighQuality": p.get('profile_pic_high_quality', ''),
                            "connected_to": p.get('connected_to', []),
                            "experiences": p.get('experiences', []),
                            "educations": p.get('educations', [])
                        })
                    
                    self.log(f"Starting AI transformation for {len(mapped_batch)} profiles...")
                    self.log(f"DEBUG: About to call process_batch_concurrent with {len(mapped_batch)} profiles")
                    self.log(f"DEBUG: First profile keys: {list(mapped_batch[0].keys()) if mapped_batch else 'none'}")
                    
                    # Run transform with explicit error handling and timeout
                    try:
                        # Add a hard timeout of 10 minutes (600 seconds)
                        self.log(f"DEBUG: Calling asyncio.wait_for with 600s timeout...")
                        results = await asyncio.wait_for(
                            process_batch_concurrent(mapped_batch),
                            timeout=600.0
                        )
                        self.log(f"DEBUG: asyncio.wait_for returned!")
                        self.log(f"AI transformation completed. Got {len(results)} results")
                    except asyncio.TimeoutError:
                        self.log(f"ERROR: AI transformation timed out after 10 minutes")
                        self.log(f"Skipping this batch of {len(mapped_batch)} profiles")
                        # Mark these profiles as transform_failed
                        failed_urls = [p.get('linkedin_url') for p in batch]
                        self.supabase.table('raw_profiles') \
                            .update({'transform_failed': True}) \
                            .in_('linkedin_url', failed_urls) \
                            .execute()
                        continue
                    except Exception as transform_error:
                        self.log(f"ERROR in AI transformation: {transform_error}")
                        import traceback
                        self.log(f"Traceback: {traceback.format_exc()}")
                        # Mark these profiles as transform_failed
                        failed_urls = [p.get('linkedin_url') for p in batch]
                        self.supabase.table('raw_profiles') \
                            .update({'transform_failed': True}) \
                            .in_('linkedin_url', failed_urls) \
                            .execute()
                        continue
                    
                    # Save to candidates
                    self.log(f"Saving {len(results)} transformed profiles to database...")
                    db_profiles = [transform_profile_for_db(p) for p in results]
                    
                    if db_profiles:
                        try:
                            self.supabase.table('candidates').upsert(db_profiles).execute()
                            self.log(f"Successfully saved {len(db_profiles)} profiles to candidates table")
                            
                            # Mark as transformed
                            processed_urls = [p['linkedin_url'] for p in db_profiles]
                            self.supabase.table('raw_profiles') \
                                .update({'transformed': True}) \
                                .in_('linkedin_url', processed_urls) \
                                .execute()
                            
                            self.log(f"Marked {len(processed_urls)} profiles as transformed")
                                
                            transformed_total += len(db_profiles)
                            self.supabase.table('upload_jobs').update({'transformed_urls': transformed_total}).eq('id', self.job_id).execute()
                            self.log(f"Progress: {transformed_total} total profiles transformed")
                            
                        except Exception as db_error:
                            self.log(f"ERROR saving to database: {db_error}")
                            import traceback
                            self.log(f"Traceback: {traceback.format_exc()}")
                    
                    # Cleanup
                    del batch
                    del mapped_batch
                    del results
                    gc.collect()
                    
                except Exception as batch_error:
                    self.log(f"ERROR processing batch: {batch_error}")
                    import traceback
                    self.log(f"Traceback: {traceback.format_exc()}")
                    # Continue to next batch instead of failing entire job
                    continue
            
            self._update_job_status('completed')
            self.log("Job completed successfully!")
            
        except Exception as e:
            self.log(f"Critical error in pipeline: {e}")
            import traceback
            self.log(traceback.format_exc())
            self._update_job_status('failed', error_message=str(e))

if __name__ == "__main__":
    # Test run
    if len(sys.argv) > 1:
        processor = StreamProcessor()
        asyncio.run(processor.run(sys.argv[1]))
    else:
        print("Usage: python stream_processor.py <csv_file>")
