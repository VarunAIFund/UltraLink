import json
import os

def clean_apify_data(input_file: str, output_file: str):
    """
    Clean Apify LinkedIn data to keep only essential fields
    """
    
    # Load company data for matching
    company_file = os.path.join(os.path.dirname(__file__), "more_companies_cleaned.json")
    company_lookup = {}
    
    try:
        with open(company_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
            for company in companies:
                url = company.get("alternate_url", "").rstrip('/')
                if url:
                    company_lookup[url] = company.get("description", "")
    except FileNotFoundError:
        print(f"Warning: {company_file} not found")
    
    # Read the original Apify data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = []
    
    for person in data:
        # Clean experiences and add company descriptions
        experiences = person.get("experiences", [])
        for experience in experiences:
            company_url = experience.get("companyLink1") or ""
            company_url = company_url.rstrip('/')
            if company_url in company_lookup:
                experience["description"] = company_lookup[company_url]
        
        cleaned_person = {
            "fullName": person.get("fullName"),
            "email": person.get("email"),
            "mobileNumber": person.get("mobileNumber"),
            "linkedinUrl": person.get("linkedinUrl"),
            "headline": person.get("headline"),
            "addressWithCountry": person.get("addressWithCountry"),
            "addressCountryOnly": person.get("addressCountryOnly"),
            "addressWithoutCountry": person.get("addressWithoutCountry"),
            "profilePic": person.get("profilePic"),
            "profilePicHighQuality": person.get("profilePicHighQuality"),
            "experiences": experiences,
            "educations": person.get("educations", [])
        }
        
        cleaned_data.append(cleaned_person)
    
    # Save cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print(f"Cleaned {len(cleaned_data)} profiles")
    print(f"Original file: {input_file}")
    print(f"Cleaned file: {output_file}")

if __name__ == "__main__":
    # Set paths relative to this script
    file_name = "test"
    script_dir = os.path.dirname(__file__)
    input_file = os.path.join(script_dir, "..", "apify", f"{file_name}.json")
    output_file = os.path.join(script_dir, f"{file_name}_cleaned.json")
    
    clean_apify_data(input_file, output_file)