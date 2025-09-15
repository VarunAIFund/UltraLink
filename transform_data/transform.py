import json
import os
from typing import List
from openai import OpenAI
from models import AIInferredProfile
from dotenv import load_dotenv
from datetime import datetime

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()

def extract_profile_data(raw_data: dict) -> dict:
    """
    Transform raw Apify LinkedIn data into structured PersonProfile using direct extraction and OpenAI for remaining fields
    """
    
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Extract fields directly from JSON data
    direct_fields = {
        "id": raw_data.get("id"),
        "contact": raw_data.get("contact"),
        "phones": raw_data.get("phones", []),
        "emails": raw_data.get("emails", []),
        "links": raw_data.get("links", []),
        "archived": raw_data.get("archived"),
        "stage": raw_data.get("stage"),
        "confidentiality": raw_data.get("confidentiality", "non-confidential"),
        "tags": raw_data.get("tags", []),
        "sources": raw_data.get("sources", []),
        "stageChanges": raw_data.get("stageChanges", []),
        "origin": raw_data.get("origin"),
        "sourcedBy": raw_data.get("sourcedBy"),
        "owner": raw_data.get("owner"),
        "followers": raw_data.get("followers", []),
        "applications": raw_data.get("applications", []),
        "createdAt": raw_data.get("createdAt"),
        "updatedAt": raw_data.get("updatedAt"),
        "lastInteractionAt": raw_data.get("lastInteractionAt"),
        "lastAdvancedAt": raw_data.get("lastAdvancedAt"),
        "snoozedUntil": raw_data.get("snoozedUntil"),
        "urls": raw_data.get("urls"),
        "isAnonymized": raw_data.get("isAnonymized"),
        "dataProtection": raw_data.get("dataProtection")
    }
    
    # Job vectors and education will be extracted and translated by GPT from parsed_resume data
    
    # Use OpenAI only for fields that need inference
    # Extract only relevant data for GPT processing
    relevant_data = {
        "name": raw_data.get("name", ""),
        "headline": raw_data.get("headline", ""),
        "location": raw_data.get("location", ""),
        "parsed_resume": {
            "positions": raw_data.get("parsed_resume", {}).get("positions", []),
            "schools": raw_data.get("parsed_resume", {}).get("schools", [])
        }
    }
    
    print(f"Sending to GPT for {raw_data.get('name', 'Unknown')}: {json.dumps(relevant_data, indent=2)}")
    
    prompt = f"""
    Based on the following candidate data, extract and infer the remaining profile information.
    IMPORTANT: All output must be in English. If any content is in any other languages, translate it to English.
    
    Candidate data:
    {json.dumps(relevant_data, indent=2)}
    
    Please extract and return a JSON object with:
    - name: Person's name
    - headline: Professional headline or current role
    - location: Location information standardized to "City, State/Province, Country" format. If any component is missing, include what's available. If remote work, use "Remote". If completely blank, leave blank.
    - seniority: Seniority level (choose from: Intern, Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level) based on titles and experience
    - skills: List of all skills including programming languages inferred from experience descriptions
    - years_experience: Total years of experience calculated from earliest date in work history up to {current_date}
    - worked_at_startup: Boolean indicating if they worked at startups. IMPORTANT: Consider the company's status at the TIME they worked there, not current status. Examples:
      * Google (founded 1998, IPO 2004): Anyone who worked there 1998-2004 = startup
    - positions: List of position objects, one for each position in work history:
      * vector_embedding: Empty string ""
      * org: Organization name
      * title: Job title
      * summary: Job summary
      * short_summary: Generate a standardized, descriptive text that summarizes this work experience in one or two sentences explaining the candidate's role and responsibilities in a narrative format. 
      * location: If completely blank, leave blank. Position location standardized to "City, State/Province, Country" format. If any component is missing, include what's available. If remote work, use "Remote".
      * industry_tags: List of relevant industry tags that describe the organization/role (e.g., "fintech", "healthcare", "edtech", "ecommerce", "saas", "ai/ml", etc.)
    - education: List of education objects with properly cleaned information:
      * school: Just the university/institution name
      * degree: Just the degree level
      * field: The field of study
    """

    # Should short summary be there if the summary is empty?
    
    response = client.responses.parse(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "Extract the structured profile information from candidate data."},
            {"role": "user", "content": prompt}
        ],
        text_format=AIInferredProfile,
    )
    
    ai_profile = response.output_parsed
    
    # Calculate average tenure: total years experience / number of positions
    num_positions = len(ai_profile.positions) if ai_profile.positions else 1  # Avoid division by zero
    average_tenure = ai_profile.years_experience / num_positions if ai_profile.years_experience else 0.0
    
    # Combine direct extraction with AI inference
    return {
        "id": direct_fields["id"],
        "name": ai_profile.name,
        "contact": direct_fields["contact"],
        "headline": ai_profile.headline,
        "stage": direct_fields["stage"],
        "confidentiality": direct_fields["confidentiality"],
        "location": ai_profile.location,
        "phones": direct_fields["phones"],
        "emails": direct_fields["emails"],
        "links": direct_fields["links"],
        "archived": direct_fields["archived"],
        "tags": direct_fields["tags"],
        "sources": direct_fields["sources"],
        "stageChanges": direct_fields["stageChanges"],
        "origin": direct_fields["origin"],
        "sourcedBy": direct_fields["sourcedBy"],
        "owner": direct_fields["owner"],
        "followers": direct_fields["followers"],
        "applications": direct_fields["applications"],
        "createdAt": direct_fields["createdAt"],
        "updatedAt": direct_fields["updatedAt"],
        "lastInteractionAt": direct_fields["lastInteractionAt"],
        "lastAdvancedAt": direct_fields["lastAdvancedAt"],
        "snoozedUntil": direct_fields["snoozedUntil"],
        "urls": direct_fields["urls"],
        "isAnonymized": direct_fields["isAnonymized"],
        "dataProtection": direct_fields["dataProtection"],
        "seniority": ai_profile.seniority,
        "skills": ai_profile.skills,
        "years_experience": ai_profile.years_experience,
        "average_tenure": average_tenure,
        "worked_at_startup": ai_profile.worked_at_startup,
        "positions": [
            {
                **pos.model_dump(),
                "start": orig_pos.get("start"),
                "end": orig_pos.get("end")
            }
            for pos, orig_pos in zip(ai_profile.positions, raw_data.get("parsed_resume", {}).get("positions", []))
        ],
        "education": [edu.model_dump() for edu in ai_profile.education]
    }

def process_candidates(input_file: str, output_file: str):
    """
    Process all candidates from input file and save structured profiles to output file
    """
    with open(input_file, 'r') as f:
        candidates = json.load(f)
    
    # Initialize output file with empty array
    with open(output_file, 'w') as f:
        json.dump([], f)
    
    processed_count = 0
    
    for i, candidate in enumerate(candidates):
        print(f"Processing candidate {i+1}/{len(candidates)}: {candidate.get('name', 'Unknown')}")
        
        try:
            profile = extract_profile_data(candidate)
            
            # Read existing profiles
            with open(output_file, 'r') as f:
                existing_profiles = json.load(f)
            
            # Add new profile
            existing_profiles.append(profile)
            
            # Write back to file immediately
            with open(output_file, 'w') as f:
                json.dump(existing_profiles, f, indent=2)
            
            processed_count += 1
            print(f"✓ Saved profile for {profile['name']} ({processed_count} total)")
            
        except Exception as e:
            print(f"✗ Error processing candidate {candidate.get('id', 'unknown')}: {str(e)}")
            continue
    
    print(f"\nProcessed {processed_count} candidates successfully")
    print(f"All profiles saved to: {output_file}")

if __name__ == "__main__":
    # Process the test data
    input_file = "test.json"
    output_file = "structured_profiles.json"
    
    process_candidates(input_file, output_file)