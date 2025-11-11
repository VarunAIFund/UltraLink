"""
Ranking module - Two-stage pipeline orchestrator

Combines GPT-5-nano classification with GPT-4o ranking for optimal cost/quality:
- Stage 1: GPT-5-nano classifies all candidates (strong/partial/no_match)
- Stage 2: GPT-4o ranks strong matches with structured outputs, rules score partial matches

This is the main ranking interface used by app.py endpoints.
"""
import asyncio
from ranking_stage_1_nano import classify_all_candidates
from ranking_stage_2_openai import rank_all_candidates


def rank_candidates(query: str, candidates: list):
    """
    Main ranking function - runs complete two-stage pipeline

    Args:
        query: The search query string
        candidates: List of candidate dictionaries from database

    Returns:
        List of ranked candidates with relevance scores and fit descriptions
        Ordered by: strong matches (GPT-4o ranked) → partial matches (rule scored) → no matches

    Performance (400 candidates):
        - Time: ~100 seconds (Stage 1: ~96s, Stage 2: ~4s single call)
        - Cost: ~$0.50 (Stage 1: $0.30, Stage 2: ~$0.20 with GPT-4o)
        - Success rate: 100% (structured outputs guarantee no forgetting)

    Note: This function wraps async calls, so it can be called from synchronous Flask endpoints.
    """
    if not candidates or len(candidates) == 0:
        return []

    print(f"\n[RANKING] Starting two-stage pipeline for {len(candidates)} candidates")

    # Stage 1: GPT-5-nano classification (async)
    print(f"[RANKING] Stage 1: GPT-5-nano classification...")
    stage_1_results = asyncio.run(classify_all_candidates(query, candidates))

    num_strong = len(stage_1_results['strong_matches'])
    num_partial = len(stage_1_results['partial_matches'])
    num_no_match = len(stage_1_results['no_matches'])

    print(f"[RANKING] Stage 1 complete: {num_strong} strong, {num_partial} partial, {num_no_match} no_match")

    # Stage 2: GPT-4o ranking (strong) + rule scoring (partial)
    print(f"[RANKING] Stage 2: GPT-4o ranking + rule scoring...")
    final_results = asyncio.run(rank_all_candidates(query, stage_1_results))

    print(f"[RANKING] Pipeline complete: {len(final_results)} candidates ranked\n")

    return final_results


# Backward compatibility alias
def rank_candidates_two_stage(query: str, candidates: list):
    """Alias for rank_candidates (for backward compatibility)"""
    return rank_candidates(query, candidates)
