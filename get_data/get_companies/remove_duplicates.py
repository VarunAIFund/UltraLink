#!/usr/bin/env python3
"""
Remove Duplicates from Companies JSON

Removes duplicate companies from companies.json based on input_linkedin_url
"""

import json
import os
from collections import defaultdict

def remove_duplicates(input_file="../results/companies.json"):
    """Remove duplicate companies based on input_linkedin_url"""
    
    print(f"🔍 Removing duplicates from: {input_file}")
    
    # Load company data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total companies loaded: {len(companies)}")
    
    # Track duplicates
    seen_urls = set()
    unique_companies = []
    duplicate_companies = []
    duplicate_groups = defaultdict(list)
    
    for company in companies:
        input_url = company.get('input_linkedin_url', 'unknown')
        
        if input_url in seen_urls:
            # This is a duplicate
            duplicate_companies.append(company)
            duplicate_groups[input_url].append(company)
        else:
            # This is unique
            seen_urls.add(input_url)
            unique_companies.append(company)
            # Add to duplicate groups for tracking (first occurrence)
            duplicate_groups[input_url].append(company)
    
    print(f"✅ Unique companies: {len(unique_companies)}")
    print(f"❌ Duplicate companies: {len(duplicate_companies)}")
    print(f"📈 Deduplication rate: {(len(duplicate_companies) / len(companies)) * 100:.1f}%")
    
    # Show duplicate analysis
    if duplicate_companies:
        print(f"\n🔍 DUPLICATE ANALYSIS:")
        duplicate_urls = [url for url, items in duplicate_groups.items() if len(items) > 1]
        print(f"URLs with duplicates: {len(duplicate_urls)}")
        
        # Show examples
        print(f"\nExamples of duplicates:")
        for i, url in enumerate(duplicate_urls[:5]):
            items = duplicate_groups[url]
            print(f"  {i+1}. {url}: {len(items)} copies")
            for j, item in enumerate(items):
                company_name = item.get('companyName', 'Unknown')
                scraped_at = item.get('scraped_at', 'Unknown')
                print(f"     Copy {j+1}: {company_name} (scraped: {scraped_at})")
        
        if len(duplicate_urls) > 5:
            print(f"     ... and {len(duplicate_urls) - 5} more duplicate URLs")
    
    # Create backup
    backup_file = input_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Created backup: {backup_file}")
    
    # Save deduplicated data
    if len(unique_companies) < len(companies):
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(unique_companies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved deduplicated data: {len(unique_companies)} unique companies")
        print(f"📄 Removed {len(duplicate_companies)} duplicates")
        
        # Save duplicates to separate file for reference
        if duplicate_companies:
            duplicates_file = input_file.replace('.json', '_duplicates.json')
            with open(duplicates_file, 'w', encoding='utf-8') as f:
                json.dump(duplicate_companies, f, indent=2, ensure_ascii=False)
            print(f"📄 Saved duplicates to: {duplicates_file}")
    else:
        print(f"✅ No duplicates found! File is already clean.")
    
    print(f"\n📈 Summary:")
    print(f"  - Original: {len(companies)} companies")
    print(f"  - Unique: {len(unique_companies)} companies")
    print(f"  - Duplicates removed: {len(duplicate_companies)} companies")
    print(f"  - Space saved: {(len(duplicate_companies) / len(companies)) * 100:.1f}%")

def analyze_duplicates_only(input_file="../results/companies.json"):
    """Analyze duplicates without removing them"""
    
    print(f"🔍 Analyzing duplicates in: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    # Track duplicates
    url_counts = defaultdict(int)
    duplicate_details = defaultdict(list)
    
    for company in companies:
        input_url = company.get('input_linkedin_url', 'unknown')
        url_counts[input_url] += 1
        if url_counts[input_url] > 1:
            duplicate_details[input_url].append({
                'company_name': company.get('companyName', 'Unknown'),
                'scraped_at': company.get('scraped_at', 'Unknown'),
                'url': company.get('url', 'Unknown')
            })
    
    duplicates = {url: count for url, count in url_counts.items() if count > 1}
    
    print(f"📊 Total companies: {len(companies)}")
    print(f"📊 Unique input URLs: {len(url_counts)}")
    print(f"❌ URLs with duplicates: {len(duplicates)}")
    print(f"❌ Total duplicate entries: {sum(duplicates.values()) - len(duplicates)}")
    
    if duplicates:
        print(f"\n🔍 TOP DUPLICATES:")
        sorted_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)
        for url, count in sorted_duplicates[:10]:
            print(f"  {url}: {count} copies")

def main():
    """Main function"""
    print("🏢 Company Deduplication Tool")
    print("=" * 50)
    
    # Ask user what they want to do
    while True:
        choice = input("\nChoose an option:\n1. Analyze duplicates only\n2. Remove duplicates\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            analyze_duplicates_only()
            break
        elif choice == "2":
            remove_duplicates()
            break
        else:
            print("Please enter 1 or 2")

if __name__ == "__main__":
    main()