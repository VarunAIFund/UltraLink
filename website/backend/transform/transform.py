#!/usr/bin/env python3
"""
AI Profile Transformation Engine

Main AI transformation engine using OpenAI GPT-5-nano structured outputs.
Transforms raw LinkedIn profiles into enhanced structured data with inferred insights
including seniority, skills, experience summaries, and company analysis.
"""

import json
import os
import sys
import asyncio
import time
import httpx
import argparse
import gc
from typing import List
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from models import AIInferredProfile
from supabase_config import get_supabase_client
from upload_to_supabase import transform_profile_for_db

# Load .env from website root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Concurrent processing configuration
BATCH_SIZE = 100  # Reduced batch size for memory safety

# Initialize Supabase client
supabase = get_supabase_client()

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
        timeout=httpx.Timeout(480.0)
    ) as http_client:
        # Create OpenAI client with custom http client
        # Increased max_retries to 8 to handle rate limits better
        client = AsyncOpenAI(
            http_client=http_client,
            max_retries=3
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
        print(f"   • Input cost: ${cost_input:.4f}")
        print(f"   • Output cost: ${cost_output:.4f}")
        print(f"   • Total tokens: {total_tokens:,}")
        print(f"   • Total cost: ${total_cost:.4f}")

    return successful_results


async def main():
    """Main async function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='AI Profile Transformation Engine')
    parser.add_argument('--auto', '--all', action='store_true',
                       help='Process all batches without prompting (for automated pipelines)')
    args = parser.parse_args()

    print(f"🚀 Starting AI Transformation Pipeline")
    print(f"   Reading from: raw_profiles table")
    print(f"   Writing to: candidates table")
    print(f"   Batch size: {BATCH_SIZE}")
    print("="*60)

    total_processed = 0
    script_start_time = time.time()
    
    while True:
        # 1. Fetch batch of unprocessed profiles from Supabase
        print(f"\nFetching next batch of {BATCH_SIZE} unprocessed profiles...")
        try:
            response = supabase.table('raw_profiles') \
                .select('*') \
                .eq('transformed', False) \
                .eq('transform_failed', False) \
                .limit(BATCH_SIZE) \
                .execute()
            
            candidates = response.data
            
            if not candidates:
                print("✅ No more unprocessed profiles found.")
                break
                
            print(f"📦 Processing batch of {len(candidates)} profiles...")
            
            # Map database fields back to structure expected by extract_profile_data
            # The raw_profiles table has snake_case fields, but extract_profile_data might expect some specific structure
            # Let's align the input data
            mapped_candidates = []
            for c in candidates:
                mapped = {
                    "linkedinUrl": c.get('linkedin_url'),
                    "fullName": c.get('full_name'),
                    "headline": c.get('headline'),
                    "addressWithCountry": c.get('location'),
                    "mobileNumber": c.get('phone'),
                    "email": c.get('email'),
                    "profilePic": c.get('profile_pic'),
                    "profilePicHighQuality": c.get('profile_pic_high_quality'),
                    "connected_to": c.get('connected_to', []),
                    "experiences": c.get('experiences', []),
                    "educations": c.get('educations', [])
                }
                mapped_candidates.append(mapped)

            # 2. Process batch with AI
            batch_results = await process_batch_concurrent(mapped_candidates)
            
            if batch_results:
                # 3. Save to candidates table
                print(f"💾 Saving {len(batch_results)} transformed profiles to candidates table...")
                
                # Transform for DB schema (candidates table)
                db_profiles = [transform_profile_for_db(p) for p in batch_results]
                
                # Filter out profiles without linkedin_url
                db_profiles = [p for p in db_profiles if p.get('linkedin_url')]
                
                # Upsert to candidates table
                try:
                    supabase.table('candidates').upsert(db_profiles).execute()
                    
                    # 4. Mark as transformed in raw_profiles
                    processed_urls = [p['linkedin_url'] for p in db_profiles]
                    
                    if processed_urls:
                        print(f"✅ Marking {len(processed_urls)} profiles as transformed...")
                        
                        # We have to update one by one or in small batches because Supabase 'in' filter has limits
                        # or we can use a loop. For now, let's just loop for safety and simplicity in error handling
                        # Optimization: Update in chunks if needed, but loop is fine for batch of 100
                        
                        # Better approach: update all in one go using 'in' filter
                        supabase.table('raw_profiles') \
                            .update({'transformed': True}) \
                            .in_('linkedin_url', processed_urls) \
                            .execute()
                            
                    total_processed += len(batch_results)
                    print(f"✨ Batch complete. Total processed: {total_processed}")
                    
                except Exception as e:
                    print(f"❌ Error saving batch to database: {e}")
                    # Mark failures if necessary, or just leave for retry
            
            # Memory cleanup
            del candidates
            del mapped_candidates
            del batch_results
            gc.collect()
            
            # Optional short pause
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            break

    total_duration = time.time() - script_start_time
    print(f"\n🎉 Pipeline completed!")
    print(f"Total processed: {total_processed}")
    print(f"Total duration: {total_duration:.1f}s")

if __name__ == "__main__":
    asyncio.run(main())