import json
import os

def clean_apify_data(input_file: str, output_file: str):
    """
    Clean Apify LinkedIn data to keep only essential fields
    """
    
    # Read the original Apify data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = []
    
    for person in data:
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
            "experiences": person.get("experiences", []),
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
    script_dir = os.path.dirname(__file__)
    input_file = os.path.join(script_dir, "..", "apify ", "large_set.json")
    output_file = os.path.join(script_dir, "large_set_cleaned.json")
    
    clean_apify_data(input_file, output_file)