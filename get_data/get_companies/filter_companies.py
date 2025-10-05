#!/usr/bin/env python3
"""
Filter Companies

Filters out companies with null descriptions from companies.json
Similar to filter_profiles but for company data
"""

import json
import os

def filter_companies(input_file="../results/companies.json"):
    """Filter companies based on description field"""
    
    print(f"🔍 Filtering companies with null descriptions: {input_file}")
    
    # Load company data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total companies loaded: {len(all_companies)}")
    
    # Separate companies
    complete_companies = []
    filtered_companies = []
    
    for company in all_companies:
        description = company.get('description')
        
        # Check if description is null, empty string, or missing
        if description is None or description == "" or description.strip() == "":
            filtered_companies.append(company)
        else:
            complete_companies.append(company)
    
    print(f"✅ Companies with descriptions: {len(complete_companies)}")
    print(f"❌ Companies with null descriptions: {len(filtered_companies)}")
    
    # Create backup
    backup_file = input_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(all_companies, f, indent=2, ensure_ascii=False)
    print(f"📄 Created backup: {backup_file}")
    
    # Save complete companies back to original file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(complete_companies, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Updated {input_file} with companies that have descriptions")
    
    # Save filtered companies to separate file
    if filtered_companies:
        filtered_file = input_file.replace('.json', '_no_description.json')
        with open(filtered_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_companies, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved companies without descriptions to: {filtered_file}")
        
        # Show examples of filtered companies
        print(f"\n🔍 Examples of companies without descriptions:")
        for i, company in enumerate(filtered_companies[:5]):
            company_name = company.get('companyName', 'Unknown')
            url = company.get('url', 'No URL')
            description = company.get('description')
            print(f"  {i+1}. {company_name}: {url}")
            print(f"     Description: {description}")
        
        if len(filtered_companies) > 5:
            print(f"     ... and {len(filtered_companies) - 5} more companies")
    else:
        print("✅ No companies without descriptions found!")
    
    # Calculate success rate
    success_rate = (len(complete_companies) / len(all_companies)) * 100 if all_companies else 0
    
    print(f"\n📈 Summary:")
    print(f"  - Kept {len(complete_companies)} companies with descriptions")
    print(f"  - Filtered out {len(filtered_companies)} companies without descriptions")
    print(f"  - Success rate: {success_rate:.1f}%")
    
    # Show some examples of companies that were kept
    if complete_companies:
        print(f"\n✅ Examples of companies that were kept:")
        for i, company in enumerate(complete_companies[:3]):
            company_name = company.get('companyName', 'Unknown')
            description = company.get('description', '')
            # Show first 100 characters of description
            short_desc = description[:100] + "..." if len(description) > 100 else description
            print(f"  {i+1}. {company_name}: \"{short_desc}\"")

def preview_filter(input_file="../results/companies.json"):
    """Preview how many companies would be filtered"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return 0, 0
    
    # Count companies that would be filtered
    filtered_count = 0
    for company in all_companies:
        description = company.get('description')
        if description is None or description == "" or description.strip() == "":
            filtered_count += 1
    
    return len(all_companies), filtered_count

def main():
    """Main function"""
    print("🏢 Company Description Filter")
    print("=" * 50)
    
    # Preview the filtering
    total_companies, companies_to_filter = preview_filter()
    
    if total_companies == 0:
        return
    
    companies_to_keep = total_companies - companies_to_filter
    
    print(f"📊 Preview:")
    print(f"  Total companies: {total_companies}")
    print(f"  Companies with descriptions (keep): {companies_to_keep}")
    print(f"  Companies without descriptions (filter): {companies_to_filter}")
    print(f"  Success rate: {(companies_to_keep / total_companies) * 100:.1f}%")
    
    # Ask for confirmation
    confirmation = input(f"\nProceed to filter out {companies_to_filter} companies with null descriptions? (y/n): ").strip().lower()
    
    if confirmation in ['y', 'yes']:
        filter_companies()
    else:
        print("❌ Operation cancelled")

if __name__ == "__main__":
    main()