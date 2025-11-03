"""
Ranking module - Two-stage pipeline orchestrator

Combines GPT-5-nano classification with Gemini ranking for optimal cost/quality:
- Stage 1: GPT-5-nano classifies all candidates (strong/partial/no_match)
- Stage 2: Gemini ranks strong matches, rules score partial matches

This is the main ranking interface used by app.py endpoints.
"""
import asyncio
from ranking_stage_1_nano import classify_all_candidates
from ranking_stage_2_gemini import rank_all_candidates


def rank_candidates(query: str, candidates: list):
    """
    Main ranking function - runs complete two-stage pipeline

    Args:
        query: The search query string
        candidates: List of candidate dictionaries from database

    Returns:
        List of ranked candidates with relevance scores and fit descriptions
        Ordered by: strong matches (Gemini ranked) → partial matches (rule scored) → no matches

    Performance (414 candidates):
        - Time: ~30-35 seconds
        - Cost: ~$0.18 ($0.16 Stage 1 + $0.02 Stage 2)
        - Success rate: 99%+

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

    # Stage 2: Gemini ranking (strong) + rule scoring (partial)
    print(f"[RANKING] Stage 2: Gemini ranking + rule scoring...")
    final_results = rank_all_candidates(query, stage_1_results)

    print(f"[RANKING] Pipeline complete: {len(final_results)} candidates ranked\n")

    return final_results


# Backward compatibility alias
def rank_candidates_two_stage(query: str, candidates: list):
    """Alias for rank_candidates (for backward compatibility)"""
    return rank_candidates(query, candidates)
