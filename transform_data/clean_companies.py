import json
import os
import csv

def load_redirect_mappings(csv_file: str) -> dict:
    """
    Load URL redirect mappings from the LinkedIn redirects CSV
    """
    redirect_mappings = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 2:
                    numeric_url = row[0]  # alternate_url column (numeric)
                    vanity_url = row[1]   # url column (vanity)
                    # Create reverse mapping: vanity_url -> numeric_url
                    redirect_mappings[vanity_url] = numeric_url
        
        print(f"✅ Loaded {len(redirect_mappings)} URL redirects from {csv_file}")
        
    except FileNotFoundError:
        print(f"Warning: {csv_file} not found, alternate_url will be empty")
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
    
    return redirect_mappings

def add_alternate_urls_from_csv(cleaned_data: list, csv_file: str) -> list:
    """
    Add alternate URLs from LinkedIn redirects CSV to cleaned company data
    """
    redirect_mappings = load_redirect_mappings(csv_file)
    
    matched_count = 0
    
    # Add alternate_url to each company by matching their vanity URL
    for company in cleaned_data:
        company_url = company.get("url", "").rstrip('/')  # Remove trailing slash for matching
        
        # Try to find this company's vanity URL in our redirect mappings
        if company_url in redirect_mappings:
            company["alternate_url"] = redirect_mappings[company_url]
            matched_count += 1
        else:
            # If no match found, leave alternate_url empty
            company["alternate_url"] = ""
            print(f"⚠️ No match found for: {company_url}")
    
    print(f"📊 Matched {matched_count} companies with redirect URLs out of {len(cleaned_data)} total")
    
    return cleaned_data

def clean_companies_data(input_file: str, output_file: str):
    """
    Clean company data to keep only essential fields
    """
    
    # Read the original company data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = []
    
    for company in data:
        cleaned_company = {
            "url": company.get("url"),
            "alternate_url": "",
            "companyName": company.get("companyName"),
            "industry": company.get("industry"),
            "tagline": company.get("tagline"),
            "description": company.get("description"),
            "logoResolutionResult": company.get("logoResolutionResult"),
            "croppedCoverImage": company.get("croppedCoverImage"),
            "specialities": company.get("specialities", []),
            "headquarter": company.get("headquarter"),
            "foundedOn": company.get("foundedOn"),
            "locations": company.get("locations", [])
        }
        
        cleaned_data.append(cleaned_company)
    
    # Add alternate URLs from LinkedIn redirects CSV
    csv_file = os.path.join(os.path.dirname(__file__), "linkedin_redirects.csv")
    cleaned_data = add_alternate_urls_from_csv(cleaned_data, csv_file)
    
    # Save cleaned data with alternate URLs
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print(f"Cleaned {len(cleaned_data)} companies with alternate URLs")
    print(f"Original file: {input_file}")
    print(f"Cleaned file: {output_file}")

if __name__ == "__main__":
    # Set paths relative to this script
    file_name = "more_companies"
    script_dir = os.path.dirname(__file__)
    input_file = os.path.join(script_dir, "..", "apify", f"{file_name}.json")
    output_file = os.path.join(script_dir, f"{file_name}_cleaned.json")
    
    clean_companies_data(input_file, output_file)