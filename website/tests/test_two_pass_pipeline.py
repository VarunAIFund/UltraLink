"""
Test the Two-Pass Classification Pipeline

Compares cost of:
1. Original single-pass approach (descriptions for ALL candidates)
2. New two-pass approach (descriptions ONLY for strong matches)

Usage:
    cd website/tests
    python test_two_pass_pipeline.py
"""
import sys
import os
import asyncio
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from search import execute_search
from ranking_stage_1_two_pass import classify_candidates_two_pass
from ranking_stage_2_gemini import rank_all_candidates


async def run_two_pass_search(query: str, connected_to: str = 'all'):
    """
    Run complete search with two-pass classification pipeline
    """
    print(f"\n{'='*70}")
    print(f"TWO-PASS SEARCH PIPELINE TEST")
    print(f"{'='*70}")
    print(f"Query: {query}")
    print(f"Connected to: {connected_to}")
    print(f"{'='*70}\n")
    
    total_start = time.time()
    
    # Step 1: SQL Generation & Database Search
    print("📊 Step 1: Generating SQL and searching database...")
    search_result = execute_search(query, connected_to)
    sql_cost = search_result.get('cost', {})
    candidates = search_result['results']
    
    print(f"\n✅ Found {len(candidates)} candidates")
    print(f"💰 SQL Generation Cost: ${sql_cost.get('total_cost', 0):.4f}")
    
    # Step 2: Two-Pass Classification
    print("\n📊 Step 2: Two-Pass Classification...")
    classification_result = await classify_candidates_two_pass(query, candidates)
    classification_cost = classification_result['cost']
    
    num_strong = len(classification_result['strong_matches'])
    num_partial = len(classification_result['partial_matches'])
    num_no_match = len(classification_result['no_matches'])
    
    # Step 3: Gemini Ranking (only for strong matches)
    print("\n📊 Step 3: Gemini Ranking (strong matches only)...")
    ranked_results, gemini_cost = rank_all_candidates(query, classification_result)
    
    # Calculate total cost
    total_sql = sql_cost.get('total_cost', 0)
    total_classification = classification_cost['total_cost']
    total_gemini = gemini_cost.get('total_cost', 0)
    total_cost = total_sql + total_classification + total_gemini
    
    total_time = time.time() - total_start
    
    # Final Summary
    print(f"\n{'='*70}")
    print(f"FINAL RESULTS")
    print(f"{'='*70}")
    print(f"   • Total candidates: {len(candidates)}")
    print(f"   • Strong matches: {num_strong}")
    print(f"   • Partial matches: {num_partial}")
    print(f"   • No matches: {num_no_match}")
    print(f"   • Total time: {total_time:.1f}s")
    
    # Detailed timing breakdown
    pass_1_time = classification_cost.get('pass_1_time', 0)
    pass_2_time = classification_cost.get('pass_2_time', 0)
    
    print(f"\n⏱️  TIMING BREAKDOWN:")
    print(f"   • Pass 1 (classification): {pass_1_time:.1f}s ({len(candidates)} candidates, {len(candidates)/pass_1_time:.1f}/sec)" if pass_1_time > 0 else "   • Pass 1: N/A")
    print(f"   • Pass 2 (descriptions):   {pass_2_time:.1f}s ({num_strong} candidates, {num_strong/pass_2_time:.1f}/sec)" if pass_2_time > 0 else "   • Pass 2: N/A")
    print(f"   • Gemini ranking:          {total_time - pass_1_time - pass_2_time:.1f}s")
    print(f"   • Total:                   {total_time:.1f}s")
    
    print(f"\n{'='*70}")
    print(f"💰 COST BREAKDOWN (TWO-PASS PIPELINE)")
    print(f"{'='*70}")
    print(f"   • SQL Generation:     ${total_sql:.4f}")
    print(f"   • Classification:")
    print(f"      - Pass 1 (quick):  ${classification_cost['pass_1']['cost']:.4f}")
    print(f"      - Pass 2 (desc):   ${classification_cost['pass_2']['cost']:.4f}")
    print(f"   • Gemini Ranking:     ${total_gemini:.4f}")
    print(f"   ────────────────────────────────")
    print(f"   • TOTAL COST:         ${total_cost:.4f}")
    print(f"{'='*70}")
    
    # Token breakdown
    print(f"\n📊 TOKEN USAGE:")
    print(f"   • Classification input:  {classification_cost['total_input_tokens']:,}")
    print(f"   • Classification output: {classification_cost['total_output_tokens']:,}")
    print(f"   • Gemini input:          {gemini_cost.get('input_tokens', 0):,}")
    print(f"   • Gemini output:         {gemini_cost.get('output_tokens', 0):,}")
    
    # Estimated savings vs original approach
    # Original approach: ~1,740 output tokens per candidate for ALL candidates
    estimated_original_output = len(candidates) * 1740
    actual_output = classification_cost['total_output_tokens']
    savings_tokens = estimated_original_output - actual_output
    savings_pct = (savings_tokens / estimated_original_output) * 100 if estimated_original_output > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"💡 ESTIMATED SAVINGS vs ORIGINAL SINGLE-PASS")
    print(f"{'='*70}")
    print(f"   • Original estimated output tokens: {estimated_original_output:,}")
    print(f"   • Two-pass actual output tokens:    {actual_output:,}")
    print(f"   • Tokens saved:                     {savings_tokens:,} ({savings_pct:.1f}%)")
    
    original_output_cost = (estimated_original_output / 1_000_000) * 0.40
    actual_output_cost = (actual_output / 1_000_000) * 0.40
    cost_saved = original_output_cost - actual_output_cost
    
    print(f"   • Original output cost:             ${original_output_cost:.4f}")
    print(f"   • Two-pass output cost:             ${actual_output_cost:.4f}")
    print(f"   • Cost saved:                       ${cost_saved:.4f}")
    print(f"{'='*70}\n")
    
    # Show sample results
    print(f"\n📋 SAMPLE STRONG MATCHES (first 5):")
    print(f"{'─'*70}")
    for i, candidate in enumerate(ranked_results[:5]):
        print(f"\n{i+1}. {candidate.get('name', 'Unknown')}")
        print(f"   Headline: {candidate.get('headline', 'N/A')}")
        print(f"   Score: {candidate.get('relevance_score', 'N/A')}")
        print(f"   Fit: {candidate.get('fit_description', 'N/A')[:150]}...")
    
    return {
        'total_cost': total_cost,
        'total_time': total_time,
        'num_strong': num_strong,
        'num_partial': num_partial,
        'num_no_match': num_no_match,
        'results': ranked_results
    }


def main():
    query = "Stanford CS graduates who worked at Google"
    
    print("\n" + "="*70)
    print("TESTING TWO-PASS CLASSIFICATION PIPELINE")
    print("="*70)
    print(f"\nQuery: {query}")
    print("\nThis test will:")
    print("  1. Search for candidates matching the query")
    print("  2. Run Pass 1: Quick classification (all candidates)")
    print("  3. Run Pass 2: Generate descriptions (strong matches only)")
    print("  4. Run Gemini ranking on strong matches")
    print("  5. Compare costs vs original approach")
    print("\n" + "="*70 + "\n")
    
    result = asyncio.run(run_two_pass_search(query))
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

