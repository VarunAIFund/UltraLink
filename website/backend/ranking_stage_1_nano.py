"""
Ranking Stage 1 - GPT-5-nano Classification
Classify candidates as strong/partial/no_match with detailed analyses
"""
import json
import os
import asyncio
from typing import Literal
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

client = AsyncOpenAI()

# Rate limiting configuration (OpenAI Usage Tier 3)
# Tier 3 limits: 5,000 RPM, 4,000,000 TPM
# Using 1,000 RPM (20% of limit) for safe buffer
MAX_REQUESTS_PER_MIN = 250
RATE_LIMIT_INTERVAL = 60 / MAX_REQUESTS_PER_MIN  # 0.06 seconds between requests

# Batch processing to prevent connection pool exhaustion
BATCH_SIZE = 250  # Process 200 candidates at a time

class CandidateClassification(BaseModel):
    """Classification result with detailed analysis"""
    match_type: Literal["strong", "partial", "no_match"] = Field(
        description="strong: closely matches query requirements | partial: some relevance but missing key elements | no_match: not relevant"
    )
    analysis: str = Field(
        description="""
        If strong match: Write a detailed 2-3 sentence analysis explaining WHY they're a strong match.
                        Include: relevant experience, key skills, seniority alignment, notable companies/education.
                        Example: "VP Engineering at Stripe with 15 years experience. Strong match because:
                        extensive healthcare tech leadership (VP @ Oscar Health 4y, Director @ One Medical 3y),
                        built multiple B2B SaaS platforms, Stanford CS degree, led ML initiatives in medical
                        imaging and patient data systems."

        If partial match: Write 1-2 sentences explaining what they're MISSING or what gaps exist.
                         Example: "Missing healthcare industry experience - background is primarily in
                         fintech and e-commerce."

        If no_match: Leave empty string ""
        """
    )
    confidence: int = Field(
        description="Confidence level 0-100. High confidence (80+) for clear matches/non-matches, lower for edge cases",
        ge=0,
        le=100
    )


async def classify_single_candidate_nano(query: str, candidate: dict, index: int):
    """
    Classify a single candidate using GPT-5-nano with detailed analysis

    Args:
        query: The search query
        candidate: Full candidate profile dict
        index: Index in original list

    Returns:
        Dict with: index, match_type, analysis, confidence, candidate
    """
    # Prepare profile summary for GPT-5-nano
    # Include full profile data - GPT-5-nano is cheap and we're running in parallel
    profile = {
        'name': candidate.get('name'),
        'headline': candidate.get('headline'),
        'seniority': candidate.get('seniority'),
        'location': candidate.get('location'),
        'skills': candidate.get('skills', []),
        'years_experience': candidate.get('years_experience'),
        'worked_at_startup': candidate.get('worked_at_startup'),
        'experiences': candidate.get('experiences', []),
        'education': candidate.get('education', [])
    }

    prompt = f"""Query: "{query}"

Analyze this candidate and classify as strong/partial/no_match.

IMPORTANT INSTRUCTIONS:
1. For STRONG matches: Write a detailed 2-3 sentence explanation of WHY they're strong
2. For PARTIAL matches: Write 1-2 sentences explaining what they're MISSING
3. For NO MATCH: Leave analysis empty ("")

Candidate Profile:
{json.dumps(profile, indent=2)}

Classify based on:
- Does their experience/skills match the query requirements?
- Is their seniority level appropriate?
- Do they have relevant industry experience?
- Are there any notable achievements or companies?"""

    try:
        # Rate limiting: wait before making API call (spaces out requests)
        await asyncio.sleep(RATE_LIMIT_INTERVAL)

        response = await client.responses.parse(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": "You are an expert recruiting analyst. Analyze candidates objectively and provide detailed insights."},
                {"role": "user", "content": prompt}
            ],
            text_format=CandidateClassification
        )

        result = response.output_parsed  # Correct attribute for GPT-5-nano structured outputs

        return {
            'index': index,
            'match_type': result.match_type,
            'analysis': result.analysis,
            'confidence': result.confidence,
            'candidate': candidate
        }

    except Exception as e:
        print(f"⚠️  Classification error for {candidate.get('name', 'Unknown')} (index {index}): {e}")
        # Return as partial match with error note on failure
        return {
            'index': index,
            'match_type': 'partial',
            'analysis': 'Classification error occurred',
            'confidence': 0,
            'candidate': candidate
        }


async def classify_all_candidates(query: str, candidates: list):
    """
    Classify all candidates in parallel using GPT-5-nano

    Args:
        query: The search query
        candidates: List of candidate dicts

    Returns:
        Dict with strong_matches, partial_matches, no_matches lists
    """
    if not candidates or len(candidates) == 0:
        return {
            'strong_matches': [],
            'partial_matches': [],
            'no_matches': []
        }

    print(f"\n🔍 Stage 1: Classifying {len(candidates)} candidates with GPT-5-nano...")
    print(f"   Rate limit: {MAX_REQUESTS_PER_MIN} requests/min ({RATE_LIMIT_INTERVAL:.2f}s interval)")
    estimated_time = len(candidates) * RATE_LIMIT_INTERVAL
    print(f"   Estimated time: ~{estimated_time:.1f} seconds")

    # Calculate number of batches
    total_batches = (len(candidates) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"   Processing in {total_batches} batch(es) of {BATCH_SIZE}")

    all_results = []

    # Process each batch sequentially
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(candidates))
        batch = candidates[start_idx:end_idx]

        print(f"\n   📦 Batch {batch_num + 1}/{total_batches}: Processing {len(batch)} candidates (indices {start_idx}-{end_idx-1})...")

        # Create async tasks for this batch only
        tasks = []
        for i, candidate in enumerate(batch):
            global_index = start_idx + i
            task = asyncio.create_task(classify_single_candidate_nano(query, candidate, global_index))
            tasks.append(task)

        # Wait for this batch to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        all_results.extend(batch_results)

        print(f"   ✓ Batch {batch_num + 1}/{total_batches} complete")

    # Use all results from all batches
    results = all_results

    # Separate into three tiers
    strong_matches = []
    partial_matches = []
    no_matches = []

    for result in results:
        if isinstance(result, Exception):
            print(f"⚠️  Task failed: {result}")
            continue

        if result['match_type'] == 'strong':
            strong_matches.append(result)
        elif result['match_type'] == 'partial':
            partial_matches.append(result)
        else:  # no_match
            no_matches.append(result)

    print(f"✅ Stage 1 Complete:")
    print(f"   • Strong matches: {len(strong_matches)}")
    print(f"   • Partial matches: {len(partial_matches)}")
    print(f"   • No matches: {len(no_matches)}")
    print(f"   • Total classified: {len(strong_matches) + len(partial_matches) + len(no_matches)}/{len(candidates)}")

    return {
        'strong_matches': strong_matches,
        'partial_matches': partial_matches,
        'no_matches': no_matches
    }


# Test function
async def test_classification():
    """Test classification with sample candidates"""
    test_candidates = [
        {
            'name': 'Jane Smith',
            'headline': 'VP Engineering at Stripe',
            'seniority': 'VP',
            'location': 'San Francisco, CA',
            'skills': ['Python', 'Leadership', 'AWS', 'ML'],
            'years_experience': 15,
            'worked_at_startup': True,
            'experiences': [
                {'org': 'Stripe', 'title': 'VP Engineering'},
                {'org': 'Square', 'title': 'Director of Engineering'}
            ],
            'education': [{'school': 'Stanford', 'degree': 'BS', 'field': 'Computer Science'}]
        },
        {
            'name': 'John Doe',
            'headline': 'Software Engineer at Google',
            'seniority': 'Senior',
            'location': 'Mountain View, CA',
            'skills': ['Java', 'C++', 'Distributed Systems'],
            'years_experience': 8,
            'worked_at_startup': False,
            'experiences': [
                {'org': 'Google', 'title': 'Senior Software Engineer'}
            ],
            'education': [{'school': 'MIT', 'degree': 'MS', 'field': 'CS'}]
        }
    ]

    query = "Find VPs in fintech with startup experience"
    results = await classify_all_candidates(query, test_candidates)

    print("\n--- Test Results ---")
    for match_type, matches in results.items():
        print(f"\n{match_type.upper()}:")
        for m in matches:
            print(f"  {m['candidate']['name']}: {m['analysis']}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_classification())
