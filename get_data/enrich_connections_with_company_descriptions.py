#!/usr/bin/env python3
"""
Enrich Connections with Company Descriptions

Adds company descriptions from companies.json to each experience in connections.json
Matches companies by normalizing LinkedIn company URLs to extract company IDs
"""

import json
import os
import re
from urllib.parse import urlparse

def normalize_company_url(url):
    """Normalize LinkedIn company URL for direct matching"""
    
    if not url or url == "null" or not isinstance(url, str):
        return None
    
    # Remove trailing slash and query parameters for consistent matching
    url = url.rstrip('/').split('?')[0]
    
    return url

def load_company_descriptions(companies_file="results/companies.json"):
    """Load company descriptions and create lookup dictionary"""
    
    print(f"📊 Loading company data from {companies_file}")
    
    try:
        with open(companies_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {companies_file}")
        return {}
    
    # Create lookup dictionary: input_linkedin_url -> description
    company_lookup = {}
    urls_processed = 0
    descriptions_available = 0
    
    for company in companies:
        input_url = company.get('input_linkedin_url')
        description = company.get('description')
        
        if input_url:
            # Normalize the input_linkedin_url for consistent matching
            normalized_input_url = normalize_company_url(input_url)
            if normalized_input_url:
                urls_processed += 1
                company_lookup[normalized_input_url] = {
                    'description': description,
                    'company_name': company.get('companyName', 'Unknown'),
                    'url': company.get('url', input_url),
                    'input_url': input_url
                }
                if description and description.strip():
                    descriptions_available += 1
    
    print(f"✅ Processed {urls_processed} companies from {len(companies)} total")
    print(f"📝 {descriptions_available} companies have descriptions available")
    
    return company_lookup

def enrich_connections(connections_file="results/connections.json"):
    """Main function to enrich connections with company descriptions"""
    
    print("🔗 LinkedIn Connections Company Description Enrichment")
    print("=" * 60)
    
    # Load company descriptions
    company_lookup = load_company_descriptions()
    
    if not company_lookup:
        print("❌ No company data available for enrichment")
        return
    
    # Load connections data
    print(f"\n📊 Loading connections data from {connections_file}")
    
    try:
        with open(connections_file, 'r', encoding='utf-8') as f:
            connections = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {connections_file}")
        return
    
    print(f"✅ Loaded {len(connections)} connections")
    
    # Statistics tracking
    stats = {
        'total_people': len(connections),
        'total_experiences': 0,
        'experiences_with_company_links': 0,
        'experiences_enriched': 0,
        'companies_not_found': 0,
        'companies_without_descriptions': 0
    }
    
    not_found_companies = set()
    enriched_examples = []
    
    # Process each person
    for person_idx, person in enumerate(connections):
        full_name = person.get('fullName', 'Unknown')
        experiences = person.get('experiences', [])
        
        for exp_idx, experience in enumerate(experiences):
            stats['total_experiences'] += 1
            
            company_link = experience.get('companyLink1')
            if company_link and company_link != "null":
                stats['experiences_with_company_links'] += 1
                
                # Normalize the companyLink1 URL to match against input_linkedin_url  
                normalized_company_link = normalize_company_url(company_link)
                
                if normalized_company_link and normalized_company_link in company_lookup:
                    company_data = company_lookup[normalized_company_link]
                    description = company_data['description']
                    
                    if description and description.strip():
                        # Add company description after caption field
                        experience['companyDescription'] = description
                        stats['experiences_enriched'] += 1
                        
                        # Collect examples for reporting
                        if len(enriched_examples) < 3:
                            enriched_examples.append({
                                'person': full_name,
                                'company': experience.get('subtitle', 'Unknown'),
                                'company_name': company_data['company_name'],
                                'description_preview': description[:100] + "..." if len(description) > 100 else description
                            })
                    else:
                        stats['companies_without_descriptions'] += 1
                else:
                    stats['companies_not_found'] += 1
                    if company_link:
                        not_found_companies.add(company_link)
        
        # Progress indicator
        if (person_idx + 1) % 100 == 0 or person_idx == len(connections) - 1:
            print(f"📈 Processed {person_idx + 1}/{len(connections)} people...")
    
    # Create backup
    backup_file = connections_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        # Need to reload original file for backup
        with open(connections_file, 'r', encoding='utf-8') as original:
            original_data = json.load(original)
        json.dump(original_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Created backup: {backup_file}")
    
    # Save enriched data
    with open(connections_file, 'w', encoding='utf-8') as f:
        json.dump(connections, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved enriched connections to: {connections_file}")
    
    # Report statistics
    print(f"\n📈 ENRICHMENT STATISTICS")
    print("=" * 40)
    print(f"Total people: {stats['total_people']}")
    print(f"Total experiences: {stats['total_experiences']}")
    print(f"Experiences with company links: {stats['experiences_with_company_links']}")
    print(f"Experiences enriched with descriptions: {stats['experiences_enriched']}")
    print(f"Companies not found in dataset: {stats['companies_not_found']}")
    print(f"Companies without descriptions: {stats['companies_without_descriptions']}")
    
    # Calculate success rate
    if stats['experiences_with_company_links'] > 0:
        success_rate = (stats['experiences_enriched'] / stats['experiences_with_company_links']) * 100
        print(f"Enrichment success rate: {success_rate:.1f}%")
    
    # Show examples of enriched data
    if enriched_examples:
        print(f"\n✅ EXAMPLES OF ENRICHED EXPERIENCES:")
        for i, example in enumerate(enriched_examples, 1):
            print(f"  {i}. {example['person']} - {example['company']}")
            print(f"     Company: {example['company_name']}")
            print(f"     Description: \"{example['description_preview']}\"")
    
    # Show companies not found (limited sample)
    if not_found_companies:
        print(f"\n❓ SAMPLE COMPANIES NOT FOUND ({len(not_found_companies)} total):")
        for i, company_url in enumerate(list(not_found_companies)[:5], 1):
            print(f"  {i}. {company_url}")
        if len(not_found_companies) > 5:
            print(f"     ... and {len(not_found_companies) - 5} more")
    
    print(f"\n🎉 ENRICHMENT COMPLETE!")
    print(f"Added company descriptions to {stats['experiences_enriched']} experiences")

def main():
    """Main function"""
    enrich_connections()

if __name__ == "__main__":
    main()