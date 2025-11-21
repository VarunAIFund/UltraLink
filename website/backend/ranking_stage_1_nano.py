"""
Ranking Stage 1 - GPT-5-nano Classification
Classify candidates as strong/partial/no_match with detailed analyses

Optimized for concurrent processing:
- Fires all requests concurrently using asyncio.gather()
- Creates fresh httpx.AsyncClient per search request (supports concurrent Flask requests)
- No artificial rate limiting (let OpenAI handle 429s with retries)
- Automatic retry for failed requests
"""
import json
import os
import asyncio
import httpx
from typing import Literal
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

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


async def classify_single_candidate_nano(query: str, candidate: dict, index: int, client: AsyncOpenAI):
    """
    Classify a single candidate using GPT-5-nano with detailed analysis

    Args:
        query: The search query
        candidate: Full candidate profile dict
        index: Index in original list
        client: AsyncOpenAI client instance

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
        response = await client.responses.parse(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": "You are an expert recruiting analyst. Analyze candidates objectively and provide detailed insights."},
                {"role": "user", "content": prompt}
            ],
            text_format=CandidateClassification
        )

        result = response.output_parsed  # Correct attribute for GPT-5-nano structured outputs

        # Track token usage for cost calculation (safely)
        # Note: responses.parse() uses input_tokens/output_tokens (not prompt_tokens/completion_tokens)
        tokens_data = {}
        try:
            if hasattr(response, 'usage') and response.usage:
                tokens_data = {
                    'input_tokens': getattr(response.usage, 'input_tokens', 0),
                    'output_tokens': getattr(response.usage, 'output_tokens', 0),
                    'total_tokens': getattr(response.usage, 'total_tokens', 0)
                }
        except Exception:
            # If token tracking fails, just skip it (don't break the classification)
            pass

        return {
            'index': index,
            'match_type': result.match_type,
            'analysis': result.analysis,
            'confidence': result.confidence,
            'candidate': candidate,
            **tokens_data  # Add token data if available
        }

    except Exception as e:
        # Don't print errors here - will be handled in classify_all_candidates
        # Return error dict instead of raising (so gather doesn't cancel others)
        return {
            'index': index,
            'match_type': 'partial',
            'analysis': 'Classification error occurred',
            'confidence': 0,
            'candidate': candidate,
            'error': str(e)  # Track error for retry logic
        }


async def classify_all_candidates(query: str, candidates: list):
    """
    Classify all candidates concurrently using GPT-5-nano

    Uses asyncio.gather() to fire all requests at once, with automatic retries
    for failures. No artificial rate limiting - OpenAI handles 429s with max_retries.

    Creates a fresh httpx/OpenAI client for this search request, allowing
    concurrent Flask requests to work without connection conflicts.

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

    import time
    start_time = time.time()

    print(f"\n🔍 Stage 1: Classifying {len(candidates)} candidates with GPT-5-nano...")
    print(f"   🚀 Firing all {len(candidates)} requests concurrently (no rate limiting)")

    # Create fresh httpx client for this request (supports concurrent Flask requests)
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

        # First pass: classify all candidates concurrently
        tasks = [
            classify_single_candidate_nano(query, candidate, i, client)
            for i, candidate in enumerate(candidates)
        ]

        # Use return_exceptions=True so one failure doesn't cancel all
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Identify failures (exceptions or confidence=0 errors)
        failed_indices = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_indices.append(i)
                print(f"⚠️  Exception for {candidates[i].get('name', 'Unknown')} (index {i}): {result}")
            elif result.get('confidence') == 0 and 'error' in result:
                failed_indices.append(i)

        # Second pass: retry failures
        if failed_indices:
            print(f"\n🔄 Retrying {len(failed_indices)} failed requests...")
            retry_tasks = [
                classify_single_candidate_nano(query, candidates[i], i, client)
                for i in failed_indices
            ]
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)

            # Replace failures with retry results
            for idx, retry_result in zip(failed_indices, retry_results):
                if isinstance(retry_result, Exception):
                    print(f"⚠️  Retry failed for {candidates[idx].get('name', 'Unknown')} (index {idx}): {retry_result}")
                    # Keep original error result
                else:
                    results[idx] = retry_result
                    if retry_result.get('confidence') > 0:
                        print(f"   ✓ Retry succeeded for {candidates[idx].get('name', 'Unknown')}")

    # Client automatically cleaned up after 'async with' block

    elapsed = time.time() - start_time

    # Separate into three tiers
    strong_matches = []
    partial_matches = []
    no_matches = []

    for result in results:
        if isinstance(result, Exception):
            continue  # Skip exceptions entirely

        if result['match_type'] == 'strong':
            strong_matches.append(result)
        elif result['match_type'] == 'partial':
            partial_matches.append(result)
        else:  # no_match
            no_matches.append(result)

    # Calculate token usage and cost (safely)
    total_input_tokens = 0
    total_output_tokens = 0
    for r in results:
        if not isinstance(r, Exception):
            total_input_tokens += r.get('input_tokens', 0)
            total_output_tokens += r.get('output_tokens', 0)

    total_tokens = total_input_tokens + total_output_tokens

    # GPT-5-nano pricing (as of 2025)
    # Input: $0.05 per 1M tokens, Output: $0.40 per 1M tokens
    cost_input = (total_input_tokens / 1_000_000) * 0.05
    cost_output = (total_output_tokens / 1_000_000) * 0.40
    total_cost = cost_input + cost_output

    print(f"\n✅ Stage 1 Complete:")
    print(f"   • Strong matches: {len(strong_matches)}")
    print(f"   • Partial matches: {len(partial_matches)}")
    print(f"   • No matches: {len(no_matches)}")
    print(f"   • Total classified: {len(strong_matches) + len(partial_matches) + len(no_matches)}/{len(candidates)}")
    print(f"   ⏱️  Time taken: {elapsed:.1f} seconds ({len(candidates)/elapsed:.1f} candidates/sec)")

    # Only show cost if we tracked any tokens
    if total_tokens > 0:
        print(f"\n💰 Stage 1 Cost:")
        print(f"   • Input tokens: {total_input_tokens:,} (${cost_input:.4f})")
        print(f"   • Output tokens: {total_output_tokens:,} (${cost_output:.4f})")
        print(f"   • Total tokens: {total_tokens:,}")
        print(f"   • Total cost: ${total_cost:.4f}")

    cost_data = {
        'input_tokens': total_input_tokens,
        'output_tokens': total_output_tokens,
        'total_tokens': total_tokens,
        'cost_input': cost_input,
        'cost_output': cost_output,
        'total_cost': total_cost
    }

    return {
        'strong_matches': strong_matches,
        'partial_matches': partial_matches,
        'no_matches': no_matches,
        'cost': cost_data
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
