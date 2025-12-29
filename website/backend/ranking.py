"""
Ranking module - Two-Pass Pipeline Orchestrator (Cost Optimized)

Uses a two-pass classification approach for optimal cost/quality:
- Pass 1: Quick classification (strong/partial/no_match) - minimal output tokens
- Pass 2: Generate descriptions ONLY for strong matches - saves ~25% on output tokens
- Stage 2: Gemini ranks strong matches, rules score partial matches

This is the main ranking interface used by app.py endpoints.
"""
import asyncio
from ranking_stage_1_two_pass import classify_candidates_two_pass
from ranking_stage_2_gemini import rank_all_candidates


def rank_candidates(query: str, candidates: list, progress_callback=None):
    """
    Main ranking function - runs complete two-pass + Gemini pipeline
    
    Two-Pass Classification (Cost Optimized):
    - Pass 1: Quick classify ALL candidates (just match_type + confidence)
    - Pass 2: Generate descriptions ONLY for strong matches
    
    Args:
        query: The search query string
        candidates: List of candidate dictionaries from database
        progress_callback: Optional callback function to report progress
    
    Returns:
        Tuple of (ranked_candidates, cost_data)
        - ranked_candidates: List ordered by strong → partial → no_match
        - cost_data: Dict with pass_1, pass_2, stage_2, and total costs
    
    Performance (500 candidates, ~200 strong matches):
        - Time: ~60-70 seconds
        - Cost: ~$0.40 (vs ~$0.55 with single-pass = 25% savings)
        - Pass 1: ~20s (26 candidates/sec)
        - Pass 2: ~40s (5 candidates/sec)
    
    Note: This function wraps async calls for synchronous Flask endpoints.
    """
    if not candidates or len(candidates) == 0:
        empty_cost = {
            'stage_1': {'input_tokens': 0, 'output_tokens': 0, 'total_cost': 0.0},
            'stage_2': {'input_tokens': 0, 'output_tokens': 0, 'total_cost': 0.0},
            'total_cost': 0.0
        }
        return [], empty_cost

    print(f"\n[RANKING] Starting two-pass pipeline for {len(candidates)} candidates")

    # Stage 1: Two-pass classification (async)
    if progress_callback:
        progress_callback('classifying', 'Analyzing candidates...')

    print(f"[RANKING] Running two-pass classification...")
    classification_results = asyncio.run(classify_candidates_two_pass(query, candidates))

    num_strong = len(classification_results['strong_matches'])
    num_partial = len(classification_results['partial_matches'])
    num_no_match = len(classification_results['no_matches'])
    classification_cost = classification_results.get('cost', {})

    print(f"[RANKING] Classification complete: {num_strong} strong, {num_partial} partial, {num_no_match} no_match")

    # Stage 2: Gemini ranking (strong) + rule scoring (partial)
    if progress_callback:
        progress_callback('ranking', 'Ranking matches...')

    print(f"[RANKING] Stage 2: Gemini ranking + rule scoring...")
    final_results, stage_2_cost = rank_all_candidates(query, classification_results)

    print(f"[RANKING] Pipeline complete: {len(final_results)} candidates ranked\n")

    # Aggregate costs - combine pass_1 and pass_2 into stage_1 for backward compatibility
    pass_1_cost = classification_cost.get('pass_1', {}).get('cost', 0.0)
    pass_2_cost = classification_cost.get('pass_2', {}).get('cost', 0.0)
    total_classification_cost = classification_cost.get('total_cost', 0.0)
    
    aggregated_cost = {
        'stage_1': {
            'pass_1_cost': pass_1_cost,
            'pass_2_cost': pass_2_cost,
            'input_tokens': classification_cost.get('total_input_tokens', 0),
            'output_tokens': classification_cost.get('total_output_tokens', 0),
            'total_cost': total_classification_cost
        },
        'stage_2': stage_2_cost,
        'total_cost': total_classification_cost + stage_2_cost.get('total_cost', 0.0)
    }

    return final_results, aggregated_cost


# Backward compatibility alias
def rank_candidates_two_stage(query: str, candidates: list):
    """Alias for rank_candidates (for backward compatibility)"""
    return rank_candidates(query, candidates)
