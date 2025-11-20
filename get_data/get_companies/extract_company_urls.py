#!/usr/bin/env python3
"""
Extract Company URLs

Extracts unique LinkedIn company URLs from all profiles in connections.json
"""

import json
import os
from collections import Counter

# Get script directory and parent directory for proper path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)  # get_data/

def extract_company_urls(input_file=None):
    """Extract unique company URLs from LinkedIn profiles"""

    # Use default path if not provided
    if input_file is None:
        input_file = os.path.join(PARENT_DIR, "results", "connections.json")

    print(f"🔍 Extracting company URLs from: {input_file}")
    
    # Load profile data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return []
    
    print(f"📊 Loaded {len(profiles)} profiles")
    
    # Extract company URLs
    company_urls = set()
    company_counter = Counter()
    profiles_with_experiences = 0
    total_experiences = 0
    
    for profile in profiles:
        experiences = profile.get('experiences', [])
        if experiences:
            profiles_with_experiences += 1
            
        for experience in experiences:
            total_experiences += 1
            
            # Extract company URL from companyLink1 field
            company_url = experience.get('companyLink1')
            if company_url:
                # Clean and standardize URL for uniqueness
                company_url = company_url.strip()
                
                # Normalize URL format
                if company_url.startswith('https://www.linkedin.com/company/'):
                    # Remove trailing slashes and query parameters for consistency
                    company_url = company_url.rstrip('/').split('?')[0]
                    company_urls.add(company_url)  # Set automatically ensures uniqueness
                    # Extract company name for counting
                    company_name = (experience.get('subtitle') or '').split(' ·')[0].strip()
                    if company_name:
                        company_counter[company_name] += 1
    
    # Convert to sorted list
    unique_company_urls = sorted(list(company_urls))
    
    print(f"\n📈 EXTRACTION RESULTS")
    print(f"=" * 50)
    print(f"Profiles with experiences: {profiles_with_experiences}")
    print(f"Total experiences: {total_experiences}")
    print(f"Total company links found: {len([url for url in company_urls])}")
    print(f"✅ UNIQUE company URLs extracted: {len(unique_company_urls)}")
    print(f"Coverage: {len(unique_company_urls)/profiles_with_experiences*100:.1f}% of profiles with experience")
    
    # Show top companies by frequency
    if company_counter:
        print(f"\n🏢 TOP COMPANIES BY FREQUENCY:")
        for company, count in company_counter.most_common(10):
            print(f"  {company}: {count} profiles")
    
    # Show sample URLs
    print(f"\n🔍 SAMPLE COMPANY URLS:")
    for url in unique_company_urls[:5]:
        print(f"  {url}")
    
    if len(unique_company_urls) > 5:
        print(f"  ... and {len(unique_company_urls) - 5} more")
    
    return unique_company_urls

def save_company_urls(company_urls, output_file=None):
    """Save company URLs to JSON file"""

    # Use default path if not provided
    if output_file is None:
        output_file = os.path.join(PARENT_DIR, "company_urls.json")

    if not company_urls:
        print("❌ No company URLs to save")
        return
    
    # Prepare data structure
    company_data = {
        "extracted_at": json.dumps({"timestamp": "2024-12-30T10:00:00"})[1:-1],  # Remove quotes
        "total_companies": len(company_urls),
        "company_urls": company_urls
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(company_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(company_urls)} company URLs to: {output_file}")

def main():
    """Main extraction function"""
    print("🏢 LinkedIn Company URL Extractor")
    print("=" * 50)
    
    # Extract company URLs
    company_urls = extract_company_urls()
    
    if not company_urls:
        print("❌ No company URLs extracted")
        return
    
    # Save to JSON file
    save_company_urls(company_urls)
    
    print(f"\n✅ Extraction complete!")
    print(f"📄 Ready for company scraping with {len(company_urls)} unique companies")

if __name__ == "__main__":
    main()