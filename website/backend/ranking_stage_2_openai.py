"""
Ranking Stage 2 - OpenAI GPT-4o Ranking with Structured Outputs
Takes output from Stage 1 (GPT-5-nano classifications) and ranks with structured outputs
Uses GPT-4o for higher quality ranking and enforces all indices are included
"""
import json
import os
import asyncio
from typing import List, Literal
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, model_validator, create_model

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

client = AsyncOpenAI()

# No rate limiting needed - single API call


def create_ranking_model(num_candidates: int):
    """
    Dynamically create a Pydantic model with score fields for each index

    This forces GPT-4o to provide a score for EVERY index.
    Each index has ONE required field:
    - index_N_score: int (0-100)

    Args:
        num_candidates: Number of candidates to rank

    Returns:
        Pydantic model class with fields index_0_score, index_1_score, index_2_score, etc.
    """
    fields = {}

    for i in range(num_candidates):
        # Score field only
        score_field = f"index_{i}_score"
        fields[score_field] = (
            int,
            Field(
                description=f"Relevance score (0-100) for candidate at index {i}. Higher = better match.",
                ge=0,
                le=100
            )
        )

    # Dynamically create the model
    RankingModel = create_model(
        'RankingModel',
        __doc__=f"Scores for all {num_candidates} candidates. Each index_N_score field is REQUIRED.",
        **fields
    )

    return RankingModel


async def rank_with_openai(query: str, summaries: list):
    """
    Rank all candidates using GPT-4o with structured output (single API call)

    Uses dynamically created Pydantic model with hardcoded fields for each index.
    This FORCES GPT-4o to provide a score for every single candidate.

    Args:
        query: The search query
        summaries: List of dicts with {index, name, analysis}

    Returns:
        List of dicts with {index, relevance_score}
        (guaranteed to include all indices 0 to N-1)
    """
    if not summaries or len(summaries) == 0:
        return []

    num_candidates = len(summaries)
    print(f"   Ranking {num_candidates} candidates with GPT-4o structured output (scores only)...")

    # Create dynamic Pydantic model with hardcoded fields for each index
    RankingModel = create_ranking_model(num_candidates)

    prompt = f"""Query: "{query}"

Rank these {num_candidates} pre-analyzed strong match candidates by relevance to the query.

Each candidate has been analyzed by a recruiting expert who explained why they're a strong match.
Your job: Assign a relevance score (0-100) to each candidate based on how well they match the query.

CRITICAL: You MUST provide a score for ALL {num_candidates} candidates.
Output format: index_N_score where N ranges from 0 to {num_candidates-1}.

Candidates to rank:
{json.dumps(summaries, indent=2)}

Scoring guidelines:
- 90-100: Perfect match
- 80-89: Very strong match with minor gaps
- 70-79: Strong match but missing aspects
- 60-69: Good match but several gaps
- 50-59: Moderate match
- Below 50: Weak match"""

    try:
        response = await client.responses.parse(
            model="gpt-4o",
            input=[
                {"role": "system", "content": "You are an expert recruiting analyst. Score candidates objectively based on query relevance. For each candidate you MUST provide a score (0-100). ALL index_N_score fields are REQUIRED."},
                {"role": "user", "content": prompt}
            ],
            text_format=RankingModel
        )

        result = response.output_parsed

        # Convert Pydantic model fields to list of rankings
        rankings = []
        for i in range(num_candidates):
            score_field = f"index_{i}_score"
            score = getattr(result, score_field)

            rankings.append({
                'index': i,
                'relevance_score': score
            })

        print(f"   ✓ Ranked {len(rankings)} candidates with scores (all {num_candidates} indices present)")

        return rankings

    except Exception as e:
        print(f"❌ Ranking error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: return default scores for ALL candidates
        print(f"   Falling back to default scores for all {num_candidates} candidates")
        fallback_rankings = []
        for i in range(num_candidates):
            fallback_rankings.append({
                'index': i,
                'relevance_score': 50
            })
        return fallback_rankings


async def rank_strong_matches_with_openai(query: str, strong_matches: list):
    """
    Rank strong matches using GPT-4o with structured outputs (single API call)

    Args:
        query: The search query
        strong_matches: List of dicts with {candidate, analysis, match_type, confidence}

    Returns:
        List of ranked candidates with relevance_score (guaranteed to include all candidates)
    """
    if not strong_matches or len(strong_matches) == 0:
        return []

    print(f"\n🎯 Stage 2A: Ranking {len(strong_matches)} strong matches with GPT-4o...")

    # Create compressed summaries (name + Stage 1 GPT-5-nano analysis)
    summaries = []
    for i, match in enumerate(strong_matches):
        candidate = match['candidate']
        summaries.append({
            'index': i,
            'name': candidate.get('name'),
            'analysis': match['analysis']  # The "why strong" from Stage 1 GPT-5-nano
        })

    # Rank all candidates in a single API call with hardcoded index fields
    rankings = await rank_with_openai(query, summaries)

    # Map rankings back to full candidates
    ranked_results = []

    for ranking in rankings:
        original_index = ranking['index']
        if 0 <= original_index < len(strong_matches):
            match = strong_matches[original_index]
            candidate = match['candidate'].copy()

            # Add Stage 1 data
            candidate['match'] = 'strong'
            candidate['fit_description'] = match['analysis']  # Stage 1's "why strong" from GPT-5-nano
            candidate['stage_1_confidence'] = match['confidence']

            # Add Stage 2 data (GPT-4o score only)
            candidate['relevance_score'] = ranking['relevance_score']

            ranked_results.append(candidate)

    # With hardcoded index fields, we're guaranteed to have all candidates
    # But let's verify anyway
    if len(ranked_results) != len(strong_matches):
        print(f"⚠️  Warning: Expected {len(strong_matches)} ranked candidates, got {len(ranked_results)}")

        # Add any missing candidates with default scores (should never happen)
        ranked_indices = set(r['index'] for r in rankings)
        for idx in range(len(strong_matches)):
            if idx not in ranked_indices:
                match = strong_matches[idx]
                candidate = match['candidate'].copy()
                candidate['match'] = 'strong'
                candidate['fit_description'] = match['analysis']
                candidate['stage_1_confidence'] = match['confidence']
                candidate['relevance_score'] = 40
                ranked_results.append(candidate)

    # Sort by relevance_score descending
    ranked_results.sort(key=lambda x: x['relevance_score'], reverse=True)

    print(f"✅ Stage 2A Complete: {len(ranked_results)} strong matches ranked")
    return ranked_results


def process_partial_matches(query: str, partial_matches: list):
    """
    Process partial matches (no scoring needed)

    Args:
        query: The search query (unused, kept for API consistency)
        partial_matches: List of dicts with {candidate, analysis, match_type}

    Returns:
        List of candidates with metadata (relevance_score = null)
    """
    if not partial_matches or len(partial_matches) == 0:
        return []

    print(f"\n📊 Stage 2B: Processing {len(partial_matches)} partial matches...")

    processed_results = []
    for match in partial_matches:
        candidate = match['candidate'].copy()

        # Add metadata (no scoring)
        candidate['match'] = 'partial'
        candidate['fit_description'] = match['analysis']  # GPT-5-nano's "what's missing"
        candidate['stage_1_confidence'] = match.get('confidence', 50)
        candidate['relevance_score'] = None  # No score for partial matches

        processed_results.append(candidate)

    print(f"✅ Stage 2B Complete: {len(processed_results)} partial matches processed")
    return processed_results


async def rank_all_candidates(query: str, stage_1_results: dict):
    """
    Complete Stage 2 ranking pipeline (async)

    Args:
        query: The search query
        stage_1_results: Dict from Stage 1 with strong_matches, partial_matches, no_matches

    Returns:
        List of all ranked candidates (strong → partial → no_match tiers)
    """
    print(f"\n{'='*60}")
    print(f"STAGE 2: RANKING & SCORING")
    print(f"{'='*60}")

    # Rank strong matches with OpenAI structured outputs
    strong_ranked = await rank_strong_matches_with_openai(
        query,
        stage_1_results['strong_matches']
    )

    # Process partial matches (no scoring)
    partial_processed = process_partial_matches(
        query,
        stage_1_results['partial_matches']
    )

    # Process no_matches (add at bottom with no score)
    no_match_list = []
    for match in stage_1_results['no_matches']:
        candidate = match['candidate'].copy()
        candidate['match'] = 'no_match'
        candidate['fit_description'] = ''
        candidate['stage_1_confidence'] = match.get('confidence', 0)
        candidate['relevance_score'] = None
        no_match_list.append(candidate)

    # Combine: strong (AI ranked) → partial (no score) → no_match
    final_results = strong_ranked + partial_processed + no_match_list

    print(f"\n{'='*60}")
    print(f"FINAL RESULTS: {len(final_results)} total candidates")
    print(f"  • Strong matches: {len(strong_ranked)} (GPT-4o ranked)")
    print(f"  • Partial matches: {len(partial_processed)} (No scoring)")
    print(f"  • No matches: {len(no_match_list)} (Filtered)")
    print(f"{'='*60}\n")

    return final_results
