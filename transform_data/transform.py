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
import httpx
from typing import List
from openai import AsyncOpenAI
from models import AIInferredProfile
from dotenv import load_dotenv
from datetime import datetime

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Concurrent processing configuration (based on ranking_stage_1_nano.py)
# Fire all requests concurrently with no artificial rate limiting
# Let OpenAI handle 429s with max_retries
BATCH_SIZE = 250  # Process 500 profiles per batch with 500 concurrent requests

async def extract_profile_data(raw_data: dict, index: int, client: AsyncOpenAI) -> dict:
    """
    Transform raw Apify LinkedIn data into structured PersonProfile using direct extraction and OpenAI for remaining fields

    Args:
        raw_data: Raw LinkedIn profile data
        index: Index in original list (for error tracking)
        client: AsyncOpenAI client instance

    Returns:
        Dict with transformed profile data or error info
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

    try:
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

        # Track token usage for cost calculation
        tokens_data = {}
        try:
            if hasattr(response, 'usage') and response.usage:
                tokens_data = {
                    'input_tokens': getattr(response.usage, 'input_tokens', 0),
                    'output_tokens': getattr(response.usage, 'output_tokens', 0),
                    'total_tokens': getattr(response.usage, 'total_tokens', 0)
                }
        except Exception:
            pass

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
            "education": [edu.model_dump() for edu in ai_profile.education],
            "index": index,
            **tokens_data
        }

    except Exception as e:
        # Return error dict instead of raising (so gather doesn't cancel others)
        return {
            'index': index,
            'linkedinUrl': direct_fields["linkedinUrl"],
            'name': raw_data.get("fullName", "Unknown"),
            'error': str(e)
        }

async def process_batch_concurrent(candidates: list) -> list:
    """
    Process a batch of candidates concurrently using GPT-5-nano (500 concurrent requests)

    Uses asyncio.gather() to fire all requests at once, with automatic retries
    for failures. No artificial rate limiting - OpenAI handles 429s with max_retries.

    Args:
        candidates: List of raw candidate dicts

    Returns:
        List of transformed profile dicts
    """
    if not candidates or len(candidates) == 0:
        return []

    start_time = time.time()

    print(f"\n🚀 Processing {len(candidates)} candidates with 500 concurrent requests...")
    print(f"   No artificial rate limiting - relying on OpenAI's retry logic")

    # Create fresh httpx client for this batch (supports concurrent processing)
    async with httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=500,
            max_keepalive_connections=100
        ),
        timeout=httpx.Timeout(120.0)
    ) as http_client:
        # Create OpenAI client with custom http client
        # Increased max_retries to 8 to handle rate limits better
        client = AsyncOpenAI(
            http_client=http_client,
            max_retries=8
        )

        # First pass: process all candidates concurrently
        tasks = [
            extract_profile_data(candidate, i, client)
            for i, candidate in enumerate(candidates)
        ]

        # Use return_exceptions=True so one failure doesn't cancel all
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Identify failures (exceptions or error field)
        failed_indices = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_indices.append(i)
                print(f"⚠️  Exception for {candidates[i].get('fullName', 'Unknown')} (index {i}): {result}")
            elif isinstance(result, dict) and 'error' in result and 'seniority' not in result:
                failed_indices.append(i)
                print(f"⚠️  Error for {result.get('name', 'Unknown')} (index {i}): {result['error']}")

        # Second pass: retry failures
        if failed_indices:
            print(f"\n🔄 Retrying {len(failed_indices)} failed requests...")
            retry_tasks = [
                extract_profile_data(candidates[i], i, client)
                for i in failed_indices
            ]
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)

            # Replace failures with retry results
            for idx, retry_result in zip(failed_indices, retry_results):
                if isinstance(retry_result, Exception):
                    print(f"⚠️  Retry failed for {candidates[idx].get('fullName', 'Unknown')} (index {idx}): {retry_result}")
                    # Keep original error result
                elif isinstance(retry_result, dict) and 'seniority' in retry_result:
                    results[idx] = retry_result
                    print(f"   ✓ Retry succeeded for {retry_result.get('name', 'Unknown')}")

    # Client automatically cleaned up after 'async with' block

    elapsed = time.time() - start_time

    # Separate successful vs failed
    successful_results = []
    failed_results = []

    for result in results:
        if isinstance(result, Exception):
            continue  # Skip exceptions entirely
        elif 'error' in result and 'seniority' not in result:
            failed_results.append(result)
        else:
            successful_results.append(result)

    # Calculate token usage and cost
    total_input_tokens = 0
    total_output_tokens = 0
    for r in successful_results:
        total_input_tokens += r.get('input_tokens', 0)
        total_output_tokens += r.get('output_tokens', 0)

    total_tokens = total_input_tokens + total_output_tokens

    # GPT-5-nano pricing (as of 2025)
    # Input: $0.05 per 1M tokens, Output: $0.40 per 1M tokens
    cost_input = (total_input_tokens / 1_000_000) * 0.05
    cost_output = (total_output_tokens / 1_000_000) * 0.40
    total_cost = cost_input + cost_output

    print(f"\n✅ Batch Complete:")
    print(f"   • Successful: {len(successful_results)}/{len(candidates)}")
    print(f"   • Failed: {len(failed_results)}")
    print(f"   ⏱️  Time taken: {elapsed:.1f} seconds ({len(candidates)/elapsed:.1f} candidates/sec)")

    # Only show cost if we tracked any tokens
    if total_tokens > 0:
        print(f"\n💰 Batch Cost:")
        print(f"   • Input tokens: {total_input_tokens:,} (${cost_input:.4f})")
        print(f"   • Output tokens: {total_output_tokens:,} (${cost_output:.4f})")
        print(f"   • Total tokens: {total_tokens:,}")
        print(f"   • Total cost: ${total_cost:.4f}")

    return successful_results


async def process_candidates(input_file: str, output_file: str):
    """
    Process all candidates from input file and save structured profiles to output file
    """
    with open(input_file, 'r') as f:
        candidates = json.load(f)

    print(f"Starting concurrent processing of {len(candidates)} candidates")
    print(f"Batch size: {BATCH_SIZE} (500 concurrent requests per batch)")
    
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
        print(f"\n{'='*60}")
        print(f"📦 BATCH {batch_num}/{len(batches)} ({len(batch_candidates)} profiles)")
        print(f"{'='*60}")

        # Process entire batch concurrently
        batch_results = await process_batch_concurrent(batch_candidates)

        # Save batch results to file (no need for duplicate checking since we pre-filtered)
        if batch_results:
            # Read existing results
            with open(output_file, 'r') as f:
                existing_results = json.load(f)

            # Remove index field before saving (was only for error tracking)
            for result in batch_results:
                result.pop('index', None)
                # Also remove token tracking fields
                result.pop('input_tokens', None)
                result.pop('output_tokens', None)
                result.pop('total_tokens', None)

            # Add all successful results (they're guaranteed to be new)
            existing_results.extend(batch_results)

            # Save back to file
            with open(output_file, 'w') as f:
                json.dump(existing_results, f, indent=2)

        total_processed += len(batch_results)
        print(f"\n💾 Saved {len(batch_results)} new entries. Total processed: {total_processed}")

        # Optional wait between batches (reduced from 60s)
        if batch_num < len(batches):
            wait_time = 10  # Reduced from 60s - can be 0 if you want
            if wait_time > 0:
                print(f"⏱️  Waiting {wait_time}s before next batch...")
                await asyncio.sleep(wait_time)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"🎉 ALL BATCHES COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {total_processed}/{len(new_candidates)}")
    print(f"Total time: {elapsed:.1f}s ({total_processed/elapsed:.1f} profiles/sec)")
    print(f"Results saved to: {output_file}")

    # Show remaining work if applicable
    if batches_to_process < total_batches_available:
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