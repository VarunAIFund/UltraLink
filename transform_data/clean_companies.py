import json
import os

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
    
    # Save cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print(f"Cleaned {len(cleaned_data)} companies")
    print(f"Original file: {input_file}")
    print(f"Cleaned file: {output_file}")

if __name__ == "__main__":
    # Set paths relative to this script
    file_name = "companies"
    script_dir = os.path.dirname(__file__)
    input_file = os.path.join(script_dir, "..", "apify", f"{file_name}.json")
    output_file = os.path.join(script_dir, f"{file_name}_cleaned.json")
    
    clean_companies_data(input_file, output_file)