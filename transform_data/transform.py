#!/usr/bin/env python3
"""
AI Profile Transformation Engine

Main AI transformation engine using OpenAI GPT-5-nano structured outputs.
Transforms raw LinkedIn profiles into enhanced structured data with inferred insights
including seniority, skills, experience summaries, and company analysis.
"""

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
    
    # Extract LinkedIn username from URL for ID
    candidate_id = f"{raw_data.get('fullName', 'candidate').replace(' ', '_')}"
    
    # Extract fields directly from JSON data
    direct_fields = {
        "id": candidate_id,
        "phone": raw_data.get("mobileNumber", ""),
        "email": raw_data.get("email", ""),
        "linkedinUrl": raw_data.get("linkedinUrl", ""),
        "profilePic": raw_data.get("profilePic", ""),
        "profilePicHighQuality": raw_data.get("profilePicHighQuality", ""),
    }
    
    # Use OpenAI only for fields that need inference
    # Extract only relevant data for GPT processing
    relevant_data = {
        "name": raw_data.get("fullName", ""),
        "headline": raw_data.get("headline", ""),
        "location": raw_data.get("addressWithCountry", ""),
        "experiences": raw_data.get("experiences", []),
        "educations": raw_data.get("educations", [])
    }
    
    print(f"Sending to GPT for {raw_data.get('fullName', 'Unknown')}: {json.dumps(relevant_data, indent=2)}")
    
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
    - experiences: List of experience objects, one for each position in work history:
      * org: Organization name (extract from subtitle field, e.g., "Google · Full-time" -> "Google")
      * company_url: Company URL (extract from companyLink1 field)
      * title: Job title
      * summary: Job summary (extract from description text components in subComponents)
      * short_summary: Generate a standardized, descriptive text that summarizes this work experience in one or two sentences explaining the candidate's role and responsibilities in a narrative format. 
      * location: Look at addressWithCountry field. If completely blank, leave blank. Position location standardized to "City, State/Province, Country" format. If any component is missing, include what's available. If remote work, use "Remote".
      * company_skills: List of technical and domain skills typically associated with working at this specific company based on experience description and implied skills (e.g., for Google: ["distributed systems", "machine learning", "cloud computing", "search algorithms"]; for Stripe: ["payments", "fintech", "API design", "financial systems"]; for Meta: ["social media", "advertising", "mobile development", "data analytics"]; for Pinecone: ["vector databases", "embeddings", "similarity search", "machine learning", "RAG", "AI infrastructure"])
      * business_model: Business model category (choose from: B2B, B2C, B2B2C, C2C, B2G) based on the company's primary business model
      * product_type: Product type category (choose from: Mobile App, Web App, Desktop App, SaaS, Platform, API/Developer Tools, E-commerce, Marketplace, Hardware, Consulting, Services) based on the company's primary product offering
      * industry_tags: List of relevant industry tags that describe the organization/role (e.g., "fintech", "healthcare", "edtech", "ecommerce", "saas", "ai/ml", etc.)
    - education: List of education objects with properly cleaned information (from educations array):
      * school: Just the university/institution name (from title field)
      * degree: Just the degree level (from subtitle field)
      * field: The field of study (from subtitle field)
    
    Note: 
    - Skip career breaks or non-work experiences when creating positions
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
    
    # Calculate average tenure: total years experience / number of experiences
    num_experiences = len(ai_profile.experiences) if ai_profile.experiences else 1  # Avoid division by zero
    average_tenure = ai_profile.years_experience / num_experiences if ai_profile.years_experience else 0.0
    
    # Combine direct extraction with AI inference
    return {
        "id": direct_fields["id"],
        "name": ai_profile.name,
        "headline": ai_profile.headline,
        "location": ai_profile.location,
        "phone": direct_fields["phone"],
        "email": direct_fields["email"],
        "connected_to": direct_fields["connected_to"],
        "linkedinUrl": direct_fields["linkedinUrl"],
        "profilePic": direct_fields["profilePic"],
        "profilePicHighQuality": direct_fields["profilePicHighQuality"],
        "seniority": ai_profile.seniority,
        "skills": ai_profile.skills,
        "years_experience": ai_profile.years_experience,
        "average_tenure": average_tenure,
        "worked_at_startup": ai_profile.worked_at_startup,
        "experiences": [exp.model_dump() for exp in ai_profile.experiences],
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
        print(f"Processing candidate {i+1}/{len(candidates)}: {candidate.get('fullName', 'Unknown')}")
        
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
            print(f"✗ Error processing candidate {candidate.get('fullName', 'unknown')}: {str(e)}")
            continue
    
    print(f"\nProcessed {processed_count} candidates successfully")
    print(f"All profiles saved to: {output_file}")

if __name__ == "__main__":
    # Process the Apify LinkedIn data
    input_file = "test_cleaned.json"
    output_file = "structured_profiles.json"
    
    process_candidates(input_file, output_file)