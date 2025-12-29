"""
Ranking Stage 1 - Two-Pass Classification (Cost Optimized)

Pass 1: Quick classification (strong/partial/no_match) with minimal output
Pass 2: Generate full descriptions ONLY for strong matches

This approach saves ~60% on output tokens by not generating descriptions
for partial/no_match candidates.
"""
import json
import os
import asyncio
import httpx
import time
from typing import Literal
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from constants import (
    RANKING_STAGE_1_MODEL,
    RANKING_STAGE_1_MAX_CONNECTIONS,
    RANKING_STAGE_1_MAX_KEEPALIVE_CONNECTIONS
)

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)


# =============================================================================
# PASS 1: Quick Classification (Minimal Output)
# =============================================================================

class QuickClassification(BaseModel):
    """Minimal classification - just the label and confidence, NO explanation"""
    match_type: Literal["strong", "partial", "no_match"] = Field(
        description="strong: closely matches query | partial: some relevance but missing key elements | no_match: not relevant"
    )
    confidence: int = Field(
        description="Confidence 0-100",
        ge=0,
        le=100
    )


async def quick_classify_single(query: str, candidate: dict, index: int, client: AsyncOpenAI):
    """
    Pass 1: Quick classification with minimal output
    """
    # Profile for classification - include education for education-based queries
    profile = {
        'name': candidate.get('name'),
        'headline': candidate.get('headline'),
        'seniority': candidate.get('seniority'),
        'location': candidate.get('location'),
        'skills': candidate.get('skills', [])[:10],  # Limit skills
        'years_experience': candidate.get('years_experience'),
        'worked_at_startup': candidate.get('worked_at_startup'),
        'experiences': [
            {'org': e.get('org'), 'title': e.get('title'), 'industry_tags': e.get('industry_tags', [])}
            for e in candidate.get('experiences', [])[:5]  # Include 5 experiences
        ],
        'education': candidate.get('education', [])  # IMPORTANT: Include education!
    }

    prompt = f"""Query: "{query}"

Classify this candidate as strong/partial/no_match.

Candidate:
{json.dumps(profile, indent=2)}

CLASSIFICATION RULES:
- STRONG: Candidate meets ALL the key requirements in the query. Look at education, work history, job titles, and companies.
- PARTIAL: Candidate meets SOME but not all requirements.
- NO_MATCH: Candidate is not relevant to the query.

IMPORTANT:
- Check EDUCATION for school/degree requirements (e.g., "Stanford CS" means check education field)
- Check EXPERIENCES for company requirements (e.g., "worked at Google" means check org field)
- Be generous - if the candidate clearly fits the query intent, mark as STRONG"""

    try:
        response = await client.responses.parse(
            model=RANKING_STAGE_1_MODEL,
            input=[
                {"role": "system", "content": "You are a recruiting analyst. Classify candidates based on how well they match the query. Be generous with STRONG matches - if the candidate clearly fits the query's main criteria, mark them STRONG."},
                {"role": "user", "content": prompt}
            ],
            text_format=QuickClassification,
            reasoning={"effort": "medium"}
        )

        result = response.output_parsed

        tokens_data = {}
        if hasattr(response, 'usage') and response.usage:
            tokens_data = {
                'input_tokens': getattr(response.usage, 'input_tokens', 0),
                'output_tokens': getattr(response.usage, 'output_tokens', 0),
            }

        return {
            'index': index,
            'match_type': result.match_type,
            'confidence': result.confidence,
            'candidate': candidate,
            **tokens_data
        }

    except Exception as e:
        return {
            'index': index,
            'match_type': 'partial',
            'confidence': 0,
            'candidate': candidate,
            'error': str(e)
        }


# =============================================================================
# PASS 2: Full Descriptions (Strong Matches Only)
# =============================================================================

class FullDescription(BaseModel):
    """Detailed description for strong matches"""
    description: str = Field(
        description="Start with candidate's name. Write 2-3 sentences explaining why they're a strong fit. Include relevant experience, skills, and accomplishments."
    )


async def generate_description_single(query: str, candidate: dict, index: int, client: AsyncOpenAI):
    """
    Pass 2: Generate full description for a strong match
    """
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

This candidate is a STRONG match. Write a 2-3 sentence description explaining why.
Start with their name. Include their most relevant experience and qualifications.

Candidate:
{json.dumps(profile, indent=2)}"""

    try:
        response = await client.responses.parse(
            model=RANKING_STAGE_1_MODEL,
            input=[
                {"role": "system", "content": "Write concise, specific descriptions highlighting why this candidate matches the query."},
                {"role": "user", "content": prompt}
            ],
            text_format=FullDescription,
            reasoning={"effort": "low"}
        )

        result = response.output_parsed

        tokens_data = {}
        if hasattr(response, 'usage') and response.usage:
            tokens_data = {
                'input_tokens': getattr(response.usage, 'input_tokens', 0),
                'output_tokens': getattr(response.usage, 'output_tokens', 0),
            }

        return {
            'index': index,
            'description': result.description,
            **tokens_data
        }

    except Exception as e:
        return {
            'index': index,
            'description': f"{candidate.get('name', 'Candidate')} matches the query criteria.",
            'error': str(e)
        }


# =============================================================================
# MAIN TWO-PASS PIPELINE
# =============================================================================

async def classify_candidates_two_pass(query: str, candidates: list, max_descriptions: int = 300):
    """
    Two-pass classification pipeline:
    - Pass 1: Quick classify ALL candidates
    - Pass 2: Generate descriptions ONLY for strong matches
    
    Args:
        query: Search query
        candidates: List of candidate dicts
        max_descriptions: Cap on descriptions to generate (cost control)
    
    Returns:
        Dict with strong_matches, partial_matches, no_matches, and cost data
    """
    if not candidates:
        return {
            'strong_matches': [],
            'partial_matches': [],
            'no_matches': [],
            'cost': {'total_cost': 0.0}
        }

    total_start = time.time()
    
    # Track costs
    pass_1_input_tokens = 0
    pass_1_output_tokens = 0
    pass_2_input_tokens = 0
    pass_2_output_tokens = 0

    # ==========================================================================
    # PASS 1: Quick Classification
    # ==========================================================================
    print(f"\n{'='*60}")
    print(f"PASS 1: Quick Classification ({len(candidates)} candidates)")
    print(f"{'='*60}")
    pass_1_start = time.time()

    async with httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=RANKING_STAGE_1_MAX_CONNECTIONS,
            max_keepalive_connections=RANKING_STAGE_1_MAX_KEEPALIVE_CONNECTIONS
        ),
        timeout=httpx.Timeout(120.0)
    ) as http_client:
        client = AsyncOpenAI(http_client=http_client, max_retries=8)

        # Classify all candidates
        tasks = [
            quick_classify_single(query, candidate, i, client)
            for i, candidate in enumerate(candidates)
        ]
        pass_1_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate results
    strong_indices = []
    partial_matches = []
    no_matches = []

    for result in pass_1_results:
        if isinstance(result, Exception):
            continue
        
        pass_1_input_tokens += result.get('input_tokens', 0)
        pass_1_output_tokens += result.get('output_tokens', 0)

        if result['match_type'] == 'strong':
            strong_indices.append(result)
        elif result['match_type'] == 'partial':
            partial_matches.append(result)
        else:
            no_matches.append(result)

    pass_1_time = time.time() - pass_1_start
    
    print(f"\n✅ Pass 1 Complete ({pass_1_time:.1f}s)")
    print(f"   • Strong: {len(strong_indices)}")
    print(f"   • Partial: {len(partial_matches)}")
    print(f"   • No match: {len(no_matches)}")

    # Calculate Pass 1 cost
    pass_1_cost_input = (pass_1_input_tokens / 1_000_000) * 0.05
    pass_1_cost_output = (pass_1_output_tokens / 1_000_000) * 0.40
    pass_1_cost = pass_1_cost_input + pass_1_cost_output

    print(f"\n💰 Pass 1 Cost:")
    print(f"   • Input tokens: {pass_1_input_tokens:,} (${pass_1_cost_input:.4f})")
    print(f"   • Output tokens: {pass_1_output_tokens:,} (${pass_1_cost_output:.4f})")
    print(f"   • Total: ${pass_1_cost:.4f}")

    # ==========================================================================
    # PASS 2: Generate Descriptions for Strong Matches
    # ==========================================================================
    strong_matches = []
    pass_2_time = 0  # Initialize in case no strong matches
    
    # Limit descriptions if needed
    candidates_for_descriptions = strong_indices[:max_descriptions]
    
    if candidates_for_descriptions:
        print(f"\n{'='*60}")
        print(f"PASS 2: Generate Descriptions ({len(candidates_for_descriptions)} strong matches)")
        print(f"{'='*60}")
        pass_2_start = time.time()

        async with httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=RANKING_STAGE_1_MAX_CONNECTIONS,
                max_keepalive_connections=RANKING_STAGE_1_MAX_KEEPALIVE_CONNECTIONS
            ),
            timeout=httpx.Timeout(120.0)
        ) as http_client:
            client = AsyncOpenAI(http_client=http_client, max_retries=8)

            # Generate descriptions
            tasks = [
                generate_description_single(query, item['candidate'], item['index'], client)
                for item in candidates_for_descriptions
            ]
            pass_2_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine Pass 1 classification with Pass 2 descriptions
        for i, desc_result in enumerate(pass_2_results):
            if isinstance(desc_result, Exception):
                continue
            
            pass_2_input_tokens += desc_result.get('input_tokens', 0)
            pass_2_output_tokens += desc_result.get('output_tokens', 0)

            # Get original classification
            classification = candidates_for_descriptions[i]
            
            strong_matches.append({
                'index': classification['index'],
                'match_type': 'strong',
                'analysis': desc_result['description'],
                'confidence': classification['confidence'],
                'candidate': classification['candidate']
            })

        pass_2_time = time.time() - pass_2_start
        print(f"\n✅ Pass 2 Complete ({pass_2_time:.1f}s)")
        print(f"   • Descriptions generated: {len(strong_matches)}")

        # Calculate Pass 2 cost
        pass_2_cost_input = (pass_2_input_tokens / 1_000_000) * 0.05
        pass_2_cost_output = (pass_2_output_tokens / 1_000_000) * 0.40
        pass_2_cost = pass_2_cost_input + pass_2_cost_output

        print(f"\n💰 Pass 2 Cost:")
        print(f"   • Input tokens: {pass_2_input_tokens:,} (${pass_2_cost_input:.4f})")
        print(f"   • Output tokens: {pass_2_output_tokens:,} (${pass_2_cost_output:.4f})")
        print(f"   • Total: ${pass_2_cost:.4f}")
    else:
        pass_2_cost = 0.0

    # Handle any strong matches beyond the cap (no descriptions)
    for item in strong_indices[max_descriptions:]:
        strong_matches.append({
            'index': item['index'],
            'match_type': 'strong',
            'analysis': f"{item['candidate'].get('name', 'Candidate')} is a strong match.",
            'confidence': item['confidence'],
            'candidate': item['candidate']
        })

    # Format partial matches (no description - just classification)
    formatted_partials = []
    for item in partial_matches:
        formatted_partials.append({
            'index': item['index'],
            'match_type': 'partial',
            'analysis': '',  # No description for partial matches
            'confidence': item['confidence'],
            'candidate': item['candidate']
        })

    # Format no matches
    formatted_no_matches = []
    for item in no_matches:
        formatted_no_matches.append({
            'index': item['index'],
            'match_type': 'no_match',
            'analysis': '',
            'confidence': item['confidence'],
            'candidate': item['candidate']
        })

    # ==========================================================================
    # FINAL SUMMARY
    # ==========================================================================
    total_time = time.time() - total_start
    total_input_tokens = pass_1_input_tokens + pass_2_input_tokens
    total_output_tokens = pass_1_output_tokens + pass_2_output_tokens
    total_cost = pass_1_cost + pass_2_cost

    print(f"\n{'='*60}")
    print(f"TWO-PASS CLASSIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"   • Total time: {total_time:.1f}s")
    print(f"   • Strong matches: {len(strong_matches)} (with descriptions)")
    print(f"   • Partial matches: {len(formatted_partials)} (gap only)")
    print(f"   • No matches: {len(formatted_no_matches)}")
    print(f"\n💰 TOTAL COST:")
    print(f"   • Pass 1 (classification): ${pass_1_cost:.4f}")
    print(f"   • Pass 2 (descriptions): ${pass_2_cost:.4f}")
    print(f"   • Input tokens: {total_input_tokens:,}")
    print(f"   • Output tokens: {total_output_tokens:,}")
    print(f"   • TOTAL: ${total_cost:.4f}")
    print(f"{'='*60}\n")

    cost_data = {
        'pass_1': {
            'input_tokens': pass_1_input_tokens,
            'output_tokens': pass_1_output_tokens,
            'cost': pass_1_cost
        },
        'pass_2': {
            'input_tokens': pass_2_input_tokens,
            'output_tokens': pass_2_output_tokens,
            'cost': pass_2_cost
        },
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_cost': total_cost,
        'pass_1_time': pass_1_time,
        'pass_2_time': pass_2_time if candidates_for_descriptions else 0,
        'total_time': total_time
    }

    return {
        'strong_matches': strong_matches,
        'partial_matches': formatted_partials,
        'no_matches': formatted_no_matches,
        'cost': cost_data
    }


# =============================================================================
# TEST FUNCTION
# =============================================================================

async def test_two_pass():
    """Test with sample candidates"""
    test_candidates = [
        {
            'name': 'Jane Smith',
            'headline': 'CEO at EdTech Startup',
            'seniority': 'C-Level',
            'location': 'San Francisco, CA',
            'skills': ['Leadership', 'Education', 'Technology'],
            'years_experience': 20,
            'worked_at_startup': True,
            'experiences': [
                {'org': 'EdTech Inc', 'title': 'CEO', 'industry_tags': ['education', 'technology']},
                {'org': 'Google', 'title': 'VP Product', 'industry_tags': ['technology']}
            ],
            'education': [{'school': 'Stanford', 'degree': 'MBA', 'field': 'Business'}]
        },
        {
            'name': 'John Doe',
            'headline': 'Software Engineer at Meta',
            'seniority': 'Senior',
            'location': 'New York, NY',
            'skills': ['Python', 'React', 'AWS'],
            'years_experience': 8,
            'worked_at_startup': False,
            'experiences': [
                {'org': 'Meta', 'title': 'Senior Software Engineer', 'industry_tags': ['technology']}
            ],
            'education': [{'school': 'MIT', 'degree': 'BS', 'field': 'CS'}]
        }
    ]

    query = "CEO with experience in education and tech"
    results = await classify_candidates_two_pass(query, test_candidates)

    print("\n--- Results ---")
    for match_type in ['strong_matches', 'partial_matches', 'no_matches']:
        print(f"\n{match_type.upper()}:")
        for m in results[match_type]:
            print(f"  {m['candidate']['name']}: {m['analysis']}")


if __name__ == "__main__":
    asyncio.run(test_two_pass())

