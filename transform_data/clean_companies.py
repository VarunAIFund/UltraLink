#!/usr/bin/env python3
import json
import os
from typing import List, Dict, Any, Optional

def clean_company_data(raw_company: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and extract specific fields from raw company data
    """
    cleaned = {}
    
    # Direct field mappings - these are copied as-is
    direct_fields = {
        'url': raw_company.get('url'),
        'companyName': raw_company.get('companyName'),
        'industry': raw_company.get('industry'),
        'tagline': raw_company.get('tagline'),
        'description': raw_company.get('description'),
        'logoResolutionResult': raw_company.get('logoResolutionResult'),
        'croppedCoverImage': raw_company.get('croppedCoverImage'),
        'specialities': raw_company.get('specialities', [])
    }
    
    # Add all direct fields (including None values for now)
    cleaned.update(direct_fields)
    
    # Handle headquarter - extract main location info
    headquarter_raw = raw_company.get('headquarter', {})
    if headquarter_raw:
        cleaned['headquarter'] = {
            'country': headquarter_raw.get('country'),
            'city': headquarter_raw.get('city'),
            'geographicArea': headquarter_raw.get('geographicArea'),
            'postalCode': headquarter_raw.get('postalCode'),
            'line1': headquarter_raw.get('line1'),
            'line2': headquarter_raw.get('line2'),
            'description': headquarter_raw.get('description')
        }
    else:
        cleaned['headquarter'] = None
    
    # Handle foundedOn - extract founding date info
    founded_raw = raw_company.get('foundedOn', {})
    if founded_raw:
        cleaned['foundedOn'] = {
            'year': founded_raw.get('year'),
            'month': founded_raw.get('month'),
            'day': founded_raw.get('day')
        }
    else:
        cleaned['foundedOn'] = None
    
    # Handle locations - keep the locations array
    locations_raw = raw_company.get('locations', [])
    if locations_raw:
        cleaned_locations = []
        for location in locations_raw:
            cleaned_location = {
                'country': location.get('country'),
                'city': location.get('city'),
                'geographicArea': location.get('geographicArea'),
                'postalCode': location.get('postalCode'),
                'line1': location.get('line1'),
                'line2': location.get('line2'),
                'description': location.get('description'),
                'headquarter': location.get('headquarter', False),
                'localizedName': location.get('localizedName'),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude')
            }
            cleaned_locations.append(cleaned_location)
        cleaned['locations'] = cleaned_locations
    else:
        cleaned['locations'] = []
    
    # Remove fields that are None to keep the JSON clean (optional)
    # Comment out the next line if you want to keep None values
    cleaned = {k: v for k, v in cleaned.items() if v is not None}
    
    return cleaned

def clean_companies_file(input_file: str, output_file: str):
    """
    Clean companies data from input file and save to output file
    """
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Loading companies data from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Handle both single company object and array of companies
        if isinstance(raw_data, dict):
            # Single company
            companies = [raw_data]
        elif isinstance(raw_data, list):
            # Array of companies
            companies = raw_data
        else:
            print("Error: Expected a company object or array of companies")
            return
        
        print(f"Processing {len(companies)} companies...")
        
        cleaned_companies = []
        success_count = 0
        
        for i, company in enumerate(companies):
            try:
                cleaned_company = clean_company_data(company)
                cleaned_companies.append(cleaned_company)
                success_count += 1
                
                company_name = cleaned_company.get('companyName', 'Unknown')
                print(f"  ✓ Processed: {company_name}")
                
            except Exception as e:
                company_name = company.get('companyName', f'Company #{i+1}')
                print(f"  ✗ Error processing {company_name}: {e}")
                continue
        
        # Save cleaned data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_companies, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== CLEANING SUMMARY ===")
        print(f"Total companies processed: {len(companies)}")
        print(f"Successfully cleaned: {success_count}")
        print(f"Failed: {len(companies) - success_count}")
        print(f"Cleaned data saved to: {output_file}")
        
        # Show sample of cleaned data
        if cleaned_companies:
            print(f"\nSample cleaned company:")
            sample = cleaned_companies[0]
            print(f"  Name: {sample.get('companyName', 'N/A')}")
            print(f"  Industry: {sample.get('industry', 'N/A')}")
            print(f"  Headquarters: {sample.get('headquarter', {}).get('city', 'N/A')}, {sample.get('headquarter', {}).get('country', 'N/A')}")
            print(f"  Founded: {sample.get('foundedOn', {}).get('year', 'N/A')}")
            print(f"  Specialties: {len(sample.get('specialities', []))} items")
            print(f"  Locations: {len(sample.get('locations', []))} locations")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error: {e}")

def analyze_fields(input_file: str):
    """
    Analyze the input file to show what fields are available
    """
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if isinstance(raw_data, dict):
            companies = [raw_data]
        elif isinstance(raw_data, list):
            companies = raw_data
        else:
            print("Error: Expected a company object or array of companies")
            return
        
        print(f"=== FIELD ANALYSIS ===")
        print(f"Found {len(companies)} companies")
        
        # Collect all unique field names
        all_fields = set()
        for company in companies:
            if isinstance(company, dict):
                all_fields.update(company.keys())
        
        print(f"\nAvailable fields ({len(all_fields)}):")
        for field in sorted(all_fields):
            # Check how many companies have this field with non-None values
            filled_count = sum(1 for c in companies if c.get(field) is not None)
            percentage = (filled_count / len(companies)) * 100
            print(f"  {field:<25} {filled_count:>3}/{len(companies)} ({percentage:5.1f}%)")
        
        # Show the fields we're extracting
        target_fields = [
            'url', 'companyName', 'industry', 'tagline', 'description',
            'headquarter', 'foundedOn', 'logoResolutionResult', 'croppedCoverImage',
            'specialities', 'locations'
        ]
        
        print(f"\nTarget fields for extraction:")
        for field in target_fields:
            if field in all_fields:
                filled_count = sum(1 for c in companies if c.get(field) is not None)
                percentage = (filled_count / len(companies)) * 100
                print(f"  ✓ {field:<25} {filled_count:>3}/{len(companies)} ({percentage:5.1f}%)")
            else:
                print(f"  ✗ {field:<25} NOT FOUND")
        
    except Exception as e:
        print(f"Error analyzing file: {e}")

def main():
    """Main function"""
    input_file = "../apify/companies.json"
    output_file = "cleaned_companies.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        print("Make sure the companies.json file exists in the apify directory.")
        return
    
    clean_companies_file(input_file, output_file)

if __name__ == "__main__":
    main()