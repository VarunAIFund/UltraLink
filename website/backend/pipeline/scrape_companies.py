#!/usr/bin/env python3
"""
Company Scraping for Pipeline

Extracts company URLs from profiles and scrapes them via Apify.
Saves directly to raw_companies Supabase table.
"""

import os
import sys
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform.supabase_config import get_supabase_client

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Apify Actor ID for company scraper
COMPANY_SCRAPER_ACTOR = "AjfNXEI9qTA2IdaAX"
BATCH_SIZE = 50  # Companies per Apify batch

def extract_company_urls_from_profiles(profiles):
    """
    Extract unique company URLs from profile experiences
    
    Args:
        profiles: List of profile dicts with experiences
    
    Returns:
        list: Unique company URLs
    """
    company_urls = set()
    
    for profile in profiles:
        experiences = profile.get('experiences', [])
        for exp in experiences:
            company_url = exp.get('companyLink1')
            if company_url and company_url != "null":
                # Normalize URL
                company_url = company_url.strip().rstrip('/').split('?')[0]
                if company_url.startswith('https://www.linkedin.com/company/'):
                    company_urls.add(company_url)
    
    return sorted(list(company_urls))

def check_existing_companies(company_urls):
    """
    Check which companies already exist in raw_companies table
    
    Args:
        company_urls: List of company URLs to check
    
    Returns:
        tuple: (urls_to_scrape, existing_count)
    """
    if not company_urls:
        return [], 0
    
    supabase = get_supabase_client()
    
    try:
        # Normalize URLs for comparison
        normalized_urls = [url.lower().rstrip('/') for url in company_urls]
        
        # Check which ones exist
        existing = set()
        page_size = 1000
        page = 0
        
        while True:
            response = supabase.table('raw_companies') \
                .select('linkedin_url') \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not response.data:
                break
            
            for item in response.data:
                url = item.get('linkedin_url', '').lower().rstrip('/')
                if url in normalized_urls:
                    existing.add(url)
            
            if len(response.data) < page_size:
                break
            
            page += 1
        
        # Filter out existing
        urls_to_scrape = [
            url for url in company_urls 
            if url.lower().rstrip('/') not in existing
        ]
        
        return urls_to_scrape, len(existing)
    
    except Exception as e:
        print(f"Warning: Could not check existing companies: {e}")
        return company_urls, 0

def scrape_companies_batch(company_urls, log_func=print):
    """
    Scrape companies via Apify and save to Supabase
    
    Args:
        company_urls: List of LinkedIn company URLs to scrape
        log_func: Logging function
    
    Returns:
        int: Number of companies scraped
    """
    if not company_urls:
        return 0
    
    log_func(f"Scraping {len(company_urls)} companies via Apify...")
    
    # Initialize Apify client
    client = ApifyClient(os.getenv('APIFY_KEY'))
    
    # Run Apify scraper
    run_input = {"profileUrls": company_urls}
    
    try:
        run = client.actor(COMPANY_SCRAPER_ACTOR).call(run_input=run_input)
        
        # Get results
        results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not results:
            log_func("No company data returned from Apify")
            return 0
        
        log_func(f"Scraped {len(results)} companies from Apify")
        
        # Save to Supabase
        return save_companies_to_supabase(results, company_urls, log_func)
    
    except Exception as e:
        log_func(f"Error scraping companies: {e}")
        return 0

def save_companies_to_supabase(companies, input_urls, log_func=print):
    """
    Save scraped companies to raw_companies table
    
    Args:
        companies: List of company dicts from Apify
        input_urls: Original input URLs (for mapping)
        log_func: Logging function
    
    Returns:
        int: Number of companies saved
    """
    if not companies:
        return 0
    
    supabase = get_supabase_client()
    current_time = datetime.now().isoformat()
    
    # Transform for database
    db_companies = []
    for i, company in enumerate(companies):
        # Map input URL (what we requested) to scraped data
        input_url = input_urls[i] if i < len(input_urls) else "unknown"
        
        # Parse founded year from foundedOn object
        founded_year = None
        if 'foundedOn' in company and isinstance(company['foundedOn'], dict):
            founded_year = company['foundedOn'].get('year')
        
        # Parse headquarters from headquarter object
        headquarters = ''
        if 'headquarter' in company and isinstance(company['headquarter'], dict):
            hq = company['headquarter']
            parts = [hq.get('city'), hq.get('geographicArea'), hq.get('country')]
            headquarters = ', '.join(filter(None, parts))
        
        # Parse company size from employeeCountRange
        company_size = ''
        if 'employeeCountRange' in company and isinstance(company['employeeCountRange'], dict):
            range_obj = company['employeeCountRange']
            start = range_obj.get('start')
            end = range_obj.get('end')
            if start and end:
                company_size = f"{start}-{end}"
        elif 'employeeCount' in company:
            company_size = str(company.get('employeeCount', ''))
        
        db_company = {
            'linkedin_url': input_url,  # Use input URL as primary key
            'name': company.get('companyName', ''),  # Company name
            'description': company.get('description', ''),
            'website': company.get('websiteUrl', ''),  # Note: websiteUrl not website
            'industry': company.get('industry', ''),
            'company_size': company_size,
            'headquarters': headquarters,
            'founded_year': founded_year,  # INTEGER
            'specialties': company.get('specialities', []),  # Note: specialities with 'i'
            'followers': company.get('followerCount', 0) or 0,  # Note: followerCount not followersCount
            'scraped_at': current_time,
            'raw_data': company  # Store full JSON for reference
        }
        
        db_companies.append(db_company)
    
    # Upsert to database
    try:
        supabase.table('raw_companies').upsert(db_companies).execute()
        log_func(f"Saved {len(db_companies)} companies to raw_companies table")
        return len(db_companies)
    except Exception as e:
        log_func(f"Error saving companies to database: {e}")
        return 0

def scrape_companies_for_profiles(profiles, log_func=print):
    """
    Main function: Extract and scrape companies for a batch of profiles
    
    Args:
        profiles: List of profile dicts
        log_func: Logging function
    
    Returns:
        dict: Stats about scraping (total, new, existing, scraped)
    """
    if not profiles:
        return {'total': 0, 'new': 0, 'existing': 0, 'scraped': 0}
    
    # Extract company URLs
    log_func(f"Extracting company URLs from {len(profiles)} profiles...")
    company_urls = extract_company_urls_from_profiles(profiles)
    
    if not company_urls:
        log_func("No company URLs found in profiles")
        return {'total': 0, 'new': 0, 'existing': 0, 'scraped': 0}
    
    log_func(f"Found {len(company_urls)} unique companies")
    
    # Check which ones already exist
    urls_to_scrape, existing_count = check_existing_companies(company_urls)
    
    log_func(f"Companies: {len(company_urls)} total, {existing_count} already exist, {len(urls_to_scrape)} to scrape")
    
    # Scrape new companies
    scraped_count = 0
    if urls_to_scrape:
        # Process in batches to avoid Apify limits
        for i in range(0, len(urls_to_scrape), BATCH_SIZE):
            batch = urls_to_scrape[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(urls_to_scrape) + BATCH_SIZE - 1) // BATCH_SIZE
            
            log_func(f"Scraping company batch {batch_num}/{total_batches} ({len(batch)} companies)...")
            scraped = scrape_companies_batch(batch, log_func)
            scraped_count += scraped
    
    return {
        'total': len(company_urls),
        'new': len(urls_to_scrape),
        'existing': existing_count,
        'scraped': scraped_count
    }

if __name__ == "__main__":
    # Test with sample profile
    test_profile = {
        'experiences': [
            {'companyLink1': 'https://www.linkedin.com/company/google'}
        ]
    }
    
    stats = scrape_companies_for_profiles([test_profile])
    print(f"\nTest stats: {stats}")
