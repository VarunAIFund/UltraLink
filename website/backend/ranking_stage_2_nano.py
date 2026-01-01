"""
Ranking Stage 2 - GPT-5-nano Ranking of Pre-Classified Candidates
Takes output from Stage 1 (GPT-5-nano classifications) and ranks with GPT-5-nano
"""
import json
import os
import asyncio
import httpx
from typing import Dict, List, Any
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

# GPT-5-nano pricing (same as Stage 1)
# Input: $0.05/1M tokens
# Output: $0.40/1M tokens

class CandidateRanking(BaseModel):
    """Ranking result for a single candidate"""
    index: int = Field(description="Index of candidate in original list")
    relevance_score: int = Field(description="Relevance score 0-100", ge=0, le=100)


class RankingResponse(BaseModel):
    """Response containing all ranked candidates"""
    ranked_candidates: List[CandidateRanking] = Field(description="List of ranked candidates with scores")


def calculate_rule_based_score(candidate: dict, query: str):
    """
    Calculate simple rule-based score for partial matches
    Returns score 0-60
    """
    score = 0

    # Skill match (0-25 points)
    skills = candidate.get('skills', [])
    if skills:
        # Simple keyword matching from query
        query_lower = query.lower()
        skill_matches = sum(1 for skill in skills if skill.lower() in query_lower)
        score += min(25, skill_matches * 5)

    # Years experience (0-15 points)
    years = candidate.get('years_experience', 0)
    score += min(15, years / 1.5)  # Max at ~22 years

    # Seniority relevance (0-10 points)
    # Simple heuristic: higher seniority = more points
    seniority = candidate.get('seniority', '').lower()
    seniority_scores = {
        'c-level': 10, 'vp': 9, 'director': 8, 'manager': 7,
        'lead': 6, 'senior': 5, 'mid': 4, 'junior': 3, 'entry': 2, 'intern': 1
    }
    score += seniority_scores.get(seniority, 0)

    # Startup experience (0-5 points)
    if 'startup' in query.lower() and candidate.get('worked_at_startup', False):
        score += 5

    # Location match (0-5 points)
    location = candidate.get('location', '').lower()
    if location:
        # Extract location keywords from query
        location_keywords = ['san francisco', 'sf', 'bay area', 'new york', 'nyc', 'seattle', 'austin', 'boston', 'remote']
        if any(loc in query.lower() for loc in location_keywords):
            if any(loc in location for loc in location_keywords):
                score += 5

    return round(score, 1)


async def rank_strong_matches_with_nano(query: str, strong_matches: list, client: AsyncOpenAI):
    """
    Rank strong matches using GPT-5-nano

    Args:
        query: The search query
        strong_matches: List of dicts with {candidate, analysis, match_type, confidence}
        client: AsyncOpenAI client instance

    Returns:
        Tuple of (ranked_results list, cost dict)
    """
    if not strong_matches or len(strong_matches) == 0:
        empty_cost = {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost_input': 0.0,
            'cost_output': 0.0,
            'total_cost': 0.0
        }
        return [], empty_cost

    print(f"\n🎯 Stage 2A: Ranking {len(strong_matches)} strong matches with GPT-5-nano...")

    # Create compressed summaries (name + GPT-5-nano analysis only)
    # This is WAY smaller than full profiles: ~300 tokens vs ~2000 tokens each
    summaries = []
    for i, match in enumerate(strong_matches):
        candidate = match['candidate']
        summaries.append({
            'index': i,
            'name': candidate.get('name'),
            'analysis': match['analysis']  # The "why strong" from GPT-5-nano Stage 1
        })

    prompt = f"""Query: "{query}"

Rank these {len(summaries)} pre-analyzed strong match candidates by relevance to the query.

Each candidate has been analyzed by a recruiting expert who explained why they're a strong match.
Your job is to rank them by relevance and assign scores.

IMPORTANT: You MUST rank ALL {len(summaries)} candidates - do not skip any.

Candidates with expert analyses:
{json.dumps(summaries, indent=2)}

For each candidate, provide:
- relevance_score (0-100): How well they match the query

Respond ONLY with valid JSON including ALL {len(summaries)} candidates:
{{
  "ranked_candidates": [
    {{
      "index": 0,
      "relevance_score": 95
    }},
    {{
      "index": 1,
      "relevance_score": 88
    }}
  ]
}}"""

    try:
        response = await client.responses.parse(
            model=RANKING_STAGE_1_MODEL,
            input=[
                {"role": "system", "content": "You are a ranking expert. Rank candidates by relevance to the search query."},
                {"role": "user", "content": prompt}
            ],
            text_format=RankingResponse,
            reasoning={"effort": "high"}
        )

        # Extract parsed response
        ranking_data = response.output_parsed

        # Track token usage and cost (responses API uses input_tokens/output_tokens)
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
            output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
        total_tokens = input_tokens + output_tokens

        # GPT-5-nano pricing: $0.05/M input, $0.40/M output
        cost_input = (input_tokens / 1_000_000) * 0.05
        cost_output = (output_tokens / 1_000_000) * 0.40
        total_cost = cost_input + cost_output

        print(f"\n💰 GPT-5-nano Ranking Cost:")
        print(f"   • Input tokens: {input_tokens:,} (${cost_input:.4f})")
        print(f"   • Output tokens: {output_tokens:,} (${cost_output:.4f})")
        print(f"   • Total tokens: {total_tokens:,}")
        print(f"   • Total cost: ${total_cost:.4f}")

        # Store cost data for return
        nano_cost = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cost_input': cost_input,
            'cost_output': cost_output,
            'total_cost': total_cost
        }

        # Map rankings back to full candidates (ranking_data is already parsed as RankingResponse)
        ranked_indices = set()
        ranked_results = []

        for ranked_item in ranking_data.ranked_candidates:
            original_index = ranked_item.index
            if 0 <= original_index < len(strong_matches):
                ranked_indices.add(original_index)

                match = strong_matches[original_index]
                candidate = match['candidate'].copy()

                # Add Stage 1 data
                candidate['match'] = 'strong'
                candidate['fit_description'] = match['analysis']  # GPT-5-nano's "why strong"
                candidate['stage_1_confidence'] = match['confidence']

                # Add Stage 2 data
                candidate['relevance_score'] = ranked_item.relevance_score

                ranked_results.append(candidate)

        # Check for missing candidates
        missing_indices = set(range(len(strong_matches))) - ranked_indices
        skipped_count = len(missing_indices)
        
        if missing_indices:
            missing_names = [strong_matches[i]['candidate'].get('name', 'Unknown') for i in sorted(missing_indices)]
            print(f"⚠️  Warning: GPT-5-nano skipped {skipped_count} candidates")

            # Add missing candidates at the end with lower scores
            for idx in sorted(missing_indices):
                match = strong_matches[idx]
                candidate = match['candidate'].copy()
                candidate['match'] = 'strong'
                candidate['fit_description'] = match['analysis']
                candidate['stage_1_confidence'] = match['confidence']
                candidate['relevance_score'] = 80  # Lower score for skipped
                ranked_results.append(candidate)

        print(f"✅ Stage 2A Complete: {len(ranked_results)} strong matches ranked")
        return ranked_results, nano_cost

    except Exception as e:
        print(f"❌ GPT-5-nano ranking error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: return strong matches with default scores
        fallback_results = []
        for match in strong_matches:
            candidate = match['candidate'].copy()
            candidate['match'] = 'strong'
            candidate['fit_description'] = match['analysis']
            candidate['stage_1_confidence'] = match['confidence']
            candidate['relevance_score'] = 50  # Default score
            fallback_results.append(candidate)

        fallback_cost = {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost_input': 0.0,
            'cost_output': 0.0,
            'total_cost': 0.0
        }
        return fallback_results, fallback_cost


def score_partial_matches(query: str, partial_matches: list):
    """
    Score partial matches with rule-based logic

    Args:
        query: The search query
        partial_matches: List of dicts with {candidate, analysis, match_type}

    Returns:
        List of scored candidates
    """
    if not partial_matches or len(partial_matches) == 0:
        return []

    print(f"\n📊 Stage 2B: Scoring {len(partial_matches)} partial matches with rules...")

    scored_results = []
    for match in partial_matches:
        candidate = match['candidate'].copy()

        # Calculate rule-based score
        score = calculate_rule_based_score(candidate, query)

        # Add metadata
        candidate['match'] = 'partial'
        candidate['fit_description'] = match['analysis']  # GPT-5-nano's "what's missing"
        candidate['stage_1_confidence'] = match.get('confidence', 50)
        candidate['relevance_score'] = score  # Rule-based score (0-60)
        candidate['ranking_rationale'] = 'Rule-based scoring (partial match)'

        scored_results.append(candidate)

    # Sort by score descending
    scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)

    print(f"✅ Stage 2B Complete: {len(scored_results)} partial matches scored")
    return scored_results


async def rank_all_candidates(query: str, stage_1_results: dict):
    """
    Complete Stage 2 ranking pipeline using GPT-5-nano

    Args:
        query: The search query
        stage_1_results: Dict from Stage 1 with strong_matches, partial_matches, no_matches

    Returns:
        Tuple of (list of all ranked candidates, cost dict)
    """
    print(f"\n{'='*60}")
    print(f"STAGE 2: RANKING & SCORING (GPT-5-nano)")
    print(f"{'='*60}")

    # Create AsyncOpenAI client (reuse same pattern as Stage 1)
    client = AsyncOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        http_client=httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=RANKING_STAGE_1_MAX_CONNECTIONS,
                max_keepalive_connections=RANKING_STAGE_1_MAX_KEEPALIVE_CONNECTIONS
            ),
            timeout=httpx.Timeout(180.0)  # 3 minutes for large ranking requests
        )
    )

    try:
        # Rank strong matches with GPT-5-nano (compressed summaries)
        strong_ranked, nano_cost = await rank_strong_matches_with_nano(
            query,
            stage_1_results['strong_matches'],
            client
        )
    finally:
        await client.close()

    # Score partial matches with rules
    partial_scored = score_partial_matches(
        query,
        stage_1_results['partial_matches']
    )

    # Process no_matches (just add at the bottom with score 0)
    no_match_list = []
    for match in stage_1_results['no_matches']:
        candidate = match['candidate'].copy()
        candidate['match'] = 'no_match'
        candidate['fit_description'] = ''
        candidate['stage_1_confidence'] = match.get('confidence', 0)
        candidate['relevance_score'] = 0
        candidate['ranking_rationale'] = 'Not relevant to query'
        no_match_list.append(candidate)

    # Combine: strong (AI ranked) → partial (rule scored) → no_match
    final_results = strong_ranked + partial_scored + no_match_list

    print(f"\n{'='*60}")
    print(f"FINAL RESULTS: {len(final_results)} total candidates")
    print(f"  • Strong matches: {len(strong_ranked)} (GPT-5-nano ranked)")
    print(f"  • Partial matches: {len(partial_scored)} (Rule scored)")
    print(f"  • No matches: {len(no_match_list)} (Filtered)")
    print(f"{'='*60}\n")

    return final_results, nano_cost


# Wrapper for synchronous interface (to match Gemini version)
def rank_all_candidates_sync(query: str, stage_1_results: dict):
    """
    Synchronous wrapper for rank_all_candidates (to match Gemini interface)
    """
    return asyncio.run(rank_all_candidates(query, stage_1_results))

