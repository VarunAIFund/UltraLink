#!/usr/bin/env python3
"""
Company Data Enrichment for Pipeline

Enriches raw profiles with company descriptions from raw_companies table.
Matches experience company URLs with company data before AI transformation.
"""

import os
import sys
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform.supabase_config import get_supabase_client

def normalize_company_url(url):
    """Normalize LinkedIn company URL for direct matching"""
    if not url or url == "null" or not isinstance(url, str):
        return None
    
    # Remove trailing slash and query parameters for consistent matching
    url = url.rstrip('/').split('?')[0].lower()
    
    return url

def load_company_descriptions_from_db():
    """
    Load company descriptions from Supabase raw_companies table
    
    Returns:
        dict: Mapping of normalized company URL to company data
    """
    supabase = get_supabase_client()
    
    company_lookup = {}
    
    try:
        # Fetch all companies from raw_companies table
        # Process in batches to handle large datasets
        page_size = 1000
        page = 0
        
        while True:
            response = supabase.table('raw_companies') \
                .select('linkedin_url, company_name, description, url') \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not response.data:
                break
            
            for company in response.data:
                linkedin_url = company.get('linkedin_url')
                if linkedin_url:
                    normalized_url = normalize_company_url(linkedin_url)
                    if normalized_url:
                        company_lookup[normalized_url] = {
                            'description': company.get('description', ''),
                            'company_name': company.get('company_name', 'Unknown'),
                            'url': company.get('url', linkedin_url)
                        }
            
            # If we got fewer than page_size, we're done
            if len(response.data) < page_size:
                break
            
            page += 1
        
        return company_lookup
    
    except Exception as e:
        print(f"Warning: Could not load company descriptions: {e}")
        print(f"Continuing without company enrichment...")
        return {}

def enrich_profile_with_companies(profile, company_lookup):
    """
    Enrich a single profile's experiences with company descriptions
    
    Args:
        profile: Profile dict with 'experiences' field
        company_lookup: Dict mapping company URLs to company data
    
    Returns:
        profile: Enriched profile dict
    """
    experiences = profile.get('experiences', [])
    enriched_count = 0
    
    for experience in experiences:
        # Get company link from experience
        company_link = experience.get('companyLink1')
        
        if company_link and company_link != "null":
            normalized_link = normalize_company_url(company_link)
            
            if normalized_link and normalized_link in company_lookup:
                company_data = company_lookup[normalized_link]
                description = company_data.get('description', '')
                
                if description and description.strip():
                    # Add company description to experience
                    experience['companyDescription'] = description
                    enriched_count += 1
    
    return profile, enriched_count

def enrich_batch_with_companies(profiles, log_func=print):
    """
    Enrich a batch of profiles with company descriptions
    
    Args:
        profiles: List of profile dicts
        log_func: Function to call for logging
    
    Returns:
        tuple: (enriched_profiles, stats_dict)
    """
    if not profiles or len(profiles) == 0:
        return profiles, {'enriched': 0, 'total_experiences': 0}
    
    log_func(f"Loading company descriptions from database...")
    
    # Load company data from Supabase
    company_lookup = load_company_descriptions_from_db()
    
    if not company_lookup:
        log_func("No company data available - skipping enrichment")
        return profiles, {'enriched': 0, 'total_experiences': 0, 'companies_loaded': 0}
    
    log_func(f"Loaded {len(company_lookup)} companies from database")
    
    # Enrich each profile
    total_enriched = 0
    total_experiences = 0
    
    for profile in profiles:
        experiences = profile.get('experiences', [])
        total_experiences += len(experiences)
        
        enriched_profile, enriched_count = enrich_profile_with_companies(profile, company_lookup)
        total_enriched += enriched_count
    
    stats = {
        'enriched': total_enriched,
        'total_experiences': total_experiences,
        'companies_loaded': len(company_lookup)
    }
    
    if total_experiences > 0:
        enrichment_rate = (total_enriched / total_experiences) * 100
        log_func(f"Company enrichment: {total_enriched}/{total_experiences} experiences ({enrichment_rate:.1f}%)")
    else:
        log_func(f"No experiences to enrich")
    
    return profiles, stats

if __name__ == "__main__":
    # Test the enrichment
    test_profile = {
        'linkedin_url': 'https://linkedin.com/in/test',
        'experiences': [
            {
                'companyLink1': 'https://www.linkedin.com/company/google',
                'title': 'Software Engineer'
            }
        ]
    }
    
    enriched, stats = enrich_batch_with_companies([test_profile])
    print(f"\nTest enrichment stats: {stats}")
    print(f"Test profile experiences: {enriched[0]['experiences']}")
