#!/usr/bin/env python3
"""
AI Profile Transformation Engine

Main AI transformation engine using OpenAI GPT-5-nano structured outputs.
Transforms raw LinkedIn profiles into enhanced structured data with inferred insights
including seniority, skills, experience summaries, and company analysis.
"""

import json
import os
import asyncio
import time
from typing import List
from openai import AsyncOpenAI
from models import AIInferredProfile
from dotenv import load_dotenv
from datetime import datetime

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = AsyncOpenAI()

# Rate limiting configuration  
# TPM limit is 200,000 tokens/min. Each profile uses 3,000-5,500 tokens (~4,000 avg).
# Using 40 req/min = 160,000 TPM (80% of limit) for 40,000 token safety buffer
MAX_REQUESTS_PER_MIN = 40
RATE_LIMIT_INTERVAL = 60 / MAX_REQUESTS_PER_MIN  # 1.5 seconds between requests
BATCH_SIZE = 40

async def extract_profile_data(raw_data: dict) -> dict:
    """
    Transform raw Apify LinkedIn data into structured PersonProfile using direct extraction and OpenAI for remaining fields
    """
    
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
        
    # Extract fields directly from JSON data
    direct_fields = {
        "connected_to": raw_data.get("connected_to", []),
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
    
  #  print(f"Sending to GPT for {raw_data.get('fullName', 'Unknown')}: {json.dumps(relevant_data, indent=2)}")
    
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
    
    # Rate limiting: wait before making API call
    await asyncio.sleep(RATE_LIMIT_INTERVAL)
    
    response = await client.responses.parse(
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
    
    # Combine company skills from all experiences to get overall skills
    all_company_skills = []
    for exp in ai_profile.experiences:
        all_company_skills.extend(exp.company_skills)
    
    # Remove duplicates while preserving order
    skills = list(dict.fromkeys(all_company_skills))
    
    # Combine direct extraction with AI inference
    return {
        "name": ai_profile.name,
        "linkedinUrl": direct_fields["linkedinUrl"],
        "headline": ai_profile.headline,
        "location": ai_profile.location,
        "phone": direct_fields["phone"],
        "email": direct_fields["email"],
        "connected_to": direct_fields["connected_to"],
        "profilePic": direct_fields["profilePic"],
        "profilePicHighQuality": direct_fields["profilePicHighQuality"],
        "seniority": ai_profile.seniority,
        "skills": skills,
        "years_experience": ai_profile.years_experience,
        "average_tenure": average_tenure,
        "worked_at_startup": ai_profile.worked_at_startup,
        "experiences": [exp.model_dump() for exp in ai_profile.experiences],
        "education": [edu.model_dump() for edu in ai_profile.education]
    }

async def process_candidates(input_file: str, output_file: str):
    """
    Process all candidates from input file and save structured profiles to output file
    """
    with open(input_file, 'r') as f:
        candidates = json.load(f)

    # Filter out profiles connected to "mary"
    candidates_before_mary_filter = len(candidates)
    candidates = [c for c in candidates if 'mary' not in c.get('connected_to', [])]
    mary_filtered_count = candidates_before_mary_filter - len(candidates)

    print(f"Starting async processing of {len(candidates)} candidates")
    print(f"Filtered out {mary_filtered_count} profiles connected to 'mary'")
    print(f"Rate limit: {MAX_REQUESTS_PER_MIN} requests/min ({RATE_LIMIT_INTERVAL:.1f}s between requests)")
    print(f"Batch size: {BATCH_SIZE}")
    
    # Initialize output file if it doesn't exist, otherwise keep existing data
    try:
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
        print(f"Found existing output file with {len(existing_data)} entries")
        # Create set of existing LinkedIn URLs for duplicate detection
        existing_urls = {result.get('linkedinUrl') for result in existing_data if result.get('linkedinUrl')}
    except FileNotFoundError:
        with open(output_file, 'w') as f:
            json.dump([], f)
        print("Created new output file")
        existing_urls = set()
    
    # Filter out candidates that already exist before processing
    new_candidates = [c for c in candidates if c.get('linkedinUrl') not in existing_urls]
    duplicates_filtered = len(candidates) - len(new_candidates)
    
    print(f"Input candidates: {len(candidates)}")
    print(f"New candidates to process: {len(new_candidates)}")
    print(f"Duplicates filtered out: {duplicates_filtered}")
    
    if not new_candidates:
        print("✅ All candidates already processed! No new work to do.")
        return
    
    # Split NEW candidates into batches
    batches = [new_candidates[i:i + BATCH_SIZE] for i in range(0, len(new_candidates), BATCH_SIZE)]
    total_batches_available = len(batches)
    
    print(f"Total batches available: {total_batches_available}")
    
    # Ask user how many batches to process
    if total_batches_available > 0:
        while True:
            try:
                user_input = input(f"\nHow many batches do you want to process? (1-{total_batches_available}, or 'all'): ").strip().lower()
                
                if user_input == 'all':
                    batches_to_process = total_batches_available
                    break
                else:
                    batches_to_process = int(user_input)
                    if 1 <= batches_to_process <= total_batches_available:
                        break
                    else:
                        print(f"Please enter a number between 1 and {total_batches_available}, or 'all'")
            except ValueError:
                print("Please enter a valid number or 'all'")
        
        # Only process the requested number of batches
        batches = batches[:batches_to_process]
        remaining_candidates = len(new_candidates) - (batches_to_process * BATCH_SIZE)
        
        print(f"\n🚀 Processing {batches_to_process} out of {total_batches_available} available batches")
        if remaining_candidates > 0:
            print(f"📋 {remaining_candidates} candidates will remain for future processing")
    else:
        batches_to_process = 0
    
    total_processed = 0
    start_time = time.time()
    
    for batch_num, batch_candidates in enumerate(batches, 1):
        print(f"\n📦 Processing batch {batch_num}/{len(batches)} ({len(batch_candidates)} profiles)")
        
        # Create tasks for this batch
        batch_tasks = []
        for i, candidate in enumerate(batch_candidates):
            print(f"  Launching {i+1}/{len(batch_candidates)}: {candidate.get('fullName', 'Unknown')}")
            
            task = asyncio.create_task(extract_profile_data(candidate))
            batch_tasks.append(task)
        
        # Wait for this batch to complete
        print(f"  ⏳ Waiting for batch {batch_num} to complete...")
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process batch results
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                failed_count += 1
                print(f"    ❌ Task {i+1} failed: {type(result).__name__}: {result}")
            else:
                successful_results.append(result)
        
        # Save batch results to file (no need for duplicate checking since we pre-filtered)
        if successful_results:
            # Read existing results
            with open(output_file, 'r') as f:
                existing_results = json.load(f)
            
            # Add all successful results (they're guaranteed to be new)
            existing_results.extend(successful_results)
            
            # Save back to file
            with open(output_file, 'w') as f:
                json.dump(existing_results, f, indent=2)
        
        total_processed += len(successful_results) if successful_results else 0
        print(f"  ✅ Batch {batch_num} complete: {len(successful_results)} successful, {failed_count} failed")
        print(f"  💾 Saved {len(successful_results)} new entries. Total processed: {total_processed}")
        
        # Wait between batches to let TPM window reset
        if batch_num < len(batches):  # Don't wait after the last batch
            print(f"  ⏱️ Waiting 60s for TPM window to reset before next batch...")
            await asyncio.sleep(60)
    
    print(f"\nCompleted {len(new_candidates) if 'batches_to_process' in locals() and batches_to_process > 0 else 0} requests in {time.time() - start_time:.1f}s")
    print(f"Final results: {total_processed} successful")
    print(f"Results saved to: {output_file}")
    
    # Show remaining work if applicable
    if 'batches_to_process' in locals() and batches_to_process < total_batches_available:
        remaining_batches = total_batches_available - batches_to_process
        remaining_candidates = len(new_candidates) - (batches_to_process * BATCH_SIZE)
        print(f"\n📋 REMAINING WORK:")
        print(f"   - {remaining_batches} batches remaining ({remaining_candidates} candidates)")
        print(f"   - Run the script again to continue processing")

async def main():
    """Main async function"""
    # Process the Apify LinkedIn data
    input_file = "../get_data/results/connections.json"
    #input_file = "test_set_new.json"
    output_file = "structured_profiles_test.json"
    
    script_start_time = time.time()
    await process_candidates(input_file, output_file)
    total_duration = time.time() - script_start_time
    
    print(f"\n🎉 Script completed successfully!")
    print(f"Total script duration: {total_duration:.1f}s")

if __name__ == "__main__":
    asyncio.run(main())