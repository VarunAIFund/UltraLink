#!/usr/bin/env python3
"""
Extract Company URLs

Extracts unique LinkedIn company URLs from profile experience data.
Creates unique_company_linkedin_urls.txt file for company data scraping pipeline.
"""

import json
import os
from typing import Set

def extract_company_urls(input_file: str, output_file: str):
    """
    Extract unique company LinkedIn URLs from experiences data
    """
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Loading data from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: Expected a list of records in the JSON file")
            return
        
        print(f"Processing {len(data):,} records...")
        
        # Set to store unique company URLs
        unique_urls: Set[str] = set()
        
        # Track statistics
        total_experiences = 0
        records_with_experiences = 0
        url_field_counts = {
            'companyLink1': 0,
            'companyLink2': 0, 
            'companyLink3': 0,
            'companyLink4': 0,
            'companyLink5': 0
        }
        
        for record in data:
            experiences = record.get('experiences', [])
            
            if experiences:
                records_with_experiences += 1
                total_experiences += len(experiences)
                
                # Extract URLs from each experience
                for experience in experiences:
                    if isinstance(experience, dict):
                        # Check all possible companyLink fields
                        for field_name in ['companyLink1', 'companyLink2', 'companyLink3', 'companyLink4', 'companyLink5']:
                            url = experience.get(field_name)
                            if url and isinstance(url, str) and url.strip():
                                clean_url = url.strip()
                                # Validate it's a LinkedIn company URL
                                if 'linkedin.com/company/' in clean_url:
                                    unique_urls.add(clean_url)
                                    url_field_counts[field_name] += 1
        
        # Sort URLs alphabetically
        sorted_urls = sorted(unique_urls)
        
        # Save to text file
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in sorted_urls:
                f.write(url + '\n')
        
        # Print statistics
        print(f"\n=== Company URL Extraction Results ===")
        print(f"Total records processed: {len(data):,}")
        print(f"Records with experiences: {records_with_experiences:,}")
        print(f"Total experiences processed: {total_experiences:,}")
        print(f"Unique company LinkedIn URLs found: {len(sorted_urls):,}")
        print(f"\nURL field distribution:")
        
        total_urls_found = sum(url_field_counts.values())
        for field, count in url_field_counts.items():
            if count > 0:
                percentage = (count / total_urls_found) * 100
                print(f"  {field}: {count:,} URLs ({percentage:.1f}%)")
        
        print(f"\nUnique company URLs saved to: {output_file}")
        
        # Show first few URLs as sample
        if sorted_urls:
            print(f"\nFirst 5 company URLs (sample):")
            for i, url in enumerate(sorted_urls[:5], 1):
                print(f"  {i}. {url}")
            
            if len(sorted_urls) > 5:
                print(f"  ... and {len(sorted_urls) - 5:,} more")
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function"""
    input_file = "../apify/test.json"
    output_file = "unique_company_linkedin_urls.txt"
    
   
    extract_company_urls(input_file, output_file)

if __name__ == "__main__":
    main()