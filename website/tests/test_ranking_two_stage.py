"""
Test Two-Stage Ranking Pipeline (GPT-5-nano → Gemini)
Compares new pipeline against current ranking_gemini.py
"""
import sys
import os
import json
import asyncio
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from search import execute_search
from ranking_stage_1_nano import classify_all_candidates
from ranking_stage_2_gemini import rank_all_candidates
from ranking_gemini import rank_candidates_gemini


def estimate_cost(num_candidates, num_strong):
    """
    Estimate cost for two-stage pipeline (based on actual measured costs)

    Stage 1 (GPT-5-nano): $0.00075829383 per candidate (measured)
    Stage 2 (Gemini): ~$0.04 per 100 strong candidates with compressed summaries
    """
    # Stage 1: GPT-5-nano classification (all candidates)
    # Actual measured cost per candidate from 211 candidate test
    STAGE_1_COST_PER_CANDIDATE = 0.00075829383
    stage_1_cost = num_candidates * STAGE_1_COST_PER_CANDIDATE

    # Stage 2: Gemini ranking (strong matches only, compressed)
    stage_2_cost = (num_strong / 100) * 0.04

    total_cost = stage_1_cost + stage_2_cost

    return {
        'stage_1_cost': stage_1_cost,
        'stage_2_cost': stage_2_cost,
        'total_cost': total_cost,
        'per_candidate': total_cost / num_candidates if num_candidates > 0 else 0
    }


async def test_two_stage_pipeline(query: str, connected_to: str = 'all', limit: int = None):
    """
    Test the complete two-stage ranking pipeline

    Args:
        query: Search query
        connected_to: Connection filter
        limit: Optional limit on number of candidates to test
    """
    print(f"\n{'='*80}")
    print(f"TWO-STAGE PIPELINE TEST")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"Connection: {connected_to}")
    if limit:
        print(f"Limit: {limit} candidates")
    print(f"{'='*80}\n")

    # Step 1: Execute search
    print("STEP 1: Executing search...")
    start_search = time.time()
    search_result = execute_search(query, connected_to=connected_to)
    search_time = time.time() - start_search

    candidates = search_result['results']
    if limit:
        candidates = candidates[:limit]

    print(f"✅ Found {len(candidates)} candidates in {search_time:.2f}s")
    print(f"   SQL: {search_result['sql'][:100]}...\n")

    # Step 2: Stage 1 - GPT-5-nano Classification
    print("STEP 2: Stage 1 Classification (GPT-5-nano)...")
    start_stage_1 = time.time()
    stage_1_results = await classify_all_candidates(query, candidates)
    stage_1_time = time.time() - start_stage_1

    num_strong = len(stage_1_results['strong_matches'])
    num_partial = len(stage_1_results['partial_matches'])
    num_no_match = len(stage_1_results['no_matches'])

    print(f"\n   Time: {stage_1_time:.2f}s")
    print(f"   Rate: {len(candidates)/stage_1_time:.1f} candidates/second\n")

    # Save Stage 1 results immediately (before Stage 2)
    stage_1_file = os.path.join(os.path.dirname(__file__), 'output', f"stage_1_results_{len(candidates)}_candidates.json")
    stage_1_data = {
        'query': query,
        'total_candidates': len(candidates),
        'stage': 'Stage 1: GPT-5-nano Classification',
        'time': stage_1_time,
        'distribution': {
            'strong': num_strong,
            'partial': num_partial,
            'no_match': num_no_match
        },
        'strong_matches': [
            {
                'index': m['index'],
                'name': m['candidate'].get('name'),
                'headline': m['candidate'].get('headline'),
                'match_type': m['match_type'],
                'analysis': m['analysis'],
                'confidence': m['confidence']
            }
            for m in stage_1_results['strong_matches']
        ],
        'partial_matches': [
            {
                'index': m['index'],
                'name': m['candidate'].get('name'),
                'headline': m['candidate'].get('headline'),
                'match_type': m['match_type'],
                'analysis': m['analysis'],
                'confidence': m['confidence']
            }
            for m in stage_1_results['partial_matches']
        ],
        'no_matches': [
            {
                'index': m['index'],
                'name': m['candidate'].get('name'),
                'match_type': m['match_type']
            }
            for m in stage_1_results['no_matches']
        ]
    }

    with open(stage_1_file, 'w') as f:
        json.dump(stage_1_data, f, indent=2)

    print(f"💾 Stage 1 results saved to: {stage_1_file}\n")

    # Step 3: Stage 2 - Gemini Ranking + Rule Scoring
    print("STEP 3: Stage 2 Ranking & Scoring...")
    start_stage_2 = time.time()
    final_results, gemini_cost = rank_all_candidates(query, stage_1_results)
    stage_2_time = time.time() - start_stage_2

    print(f"   Time: {stage_2_time:.2f}s")

    # Check if Gemini ranked all strong matches (using LinkedIn URLs as unique identifiers)
    strong_input_count = num_strong
    strong_output = [r for r in final_results if r.get('match') == 'strong']
    strong_output_count = len(strong_output)

    print(f"\n   🔍 Gemini Completeness Check:")
    print(f"      Input:  {strong_input_count} strong matches")
    print(f"      Output: {strong_output_count} strong matches")

    # Compare actual LinkedIn URLs (unique identifiers), not just counts
    input_urls = {m['candidate'].get('linkedin_url') for m in stage_1_results['strong_matches']}
    output_urls = {r.get('linkedin_url') for r in strong_output}

    # Find missing and extra candidates
    missing_urls = input_urls - output_urls
    extra_urls = output_urls - input_urls

    if len(missing_urls) == 0 and len(extra_urls) == 0:
        print(f"      ✅ Perfect match - all strong matches ranked correctly!")
    else:
        if missing_urls:
            print(f"      ⚠️  Missing: {len(missing_urls)} candidates Gemini skipped")
            # Get names for missing candidates
            missing_candidates = [m['candidate'] for m in stage_1_results['strong_matches']
                                if m['candidate'].get('linkedin_url') in missing_urls]
            missing_names = [c.get('name', 'Unknown') for c in missing_candidates[:5]]
            print(f"         Candidates: {', '.join(missing_names)}")
            if len(missing_urls) > 5:
                print(f"         ... and {len(missing_urls) - 5} more")

        if extra_urls:
            print(f"      ⚠️  Extra: {len(extra_urls)} candidates not in input")
            # Get names for extra candidates
            extra_candidates = [r for r in strong_output if r.get('linkedin_url') in extra_urls]
            extra_names = [c.get('name', 'Unknown') for c in extra_candidates[:5]]
            print(f"         Candidates: {', '.join(extra_names)}")
    print()

    # Calculate totals
    total_time = search_time + stage_1_time + stage_2_time
    pipeline_time = stage_1_time + stage_2_time

    # Cost estimates
    costs = estimate_cost(len(candidates), num_strong)

    # Summary
    print(f"\n{'='*80}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'='*80}")
    print(f"Total Time:      {total_time:.2f}s")
    print(f"  - Search:      {search_time:.2f}s")
    print(f"  - Stage 1:     {stage_1_time:.2f}s ({len(candidates)/stage_1_time:.1f} cand/s)")
    print(f"  - Stage 2:     {stage_2_time:.2f}s")
    print(f"\nEstimated Cost:  ${costs['total_cost']:.4f}")
    print(f"  - Stage 1:     ${costs['stage_1_cost']:.4f}")
    print(f"  - Stage 2:     ${costs['stage_2_cost']:.4f}")
    print(f"  - Per Cand:    ${costs['per_candidate']:.5f}")
    print(f"\nCandidates:      {len(candidates)} total")
    print(f"  - Strong:      {num_strong} ({num_strong/len(candidates)*100:.1f}%)")
    print(f"  - Partial:     {num_partial} ({num_partial/len(candidates)*100:.1f}%)")
    print(f"  - No Match:    {num_no_match} ({num_no_match/len(candidates)*100:.1f}%)")
    print(f"{'='*80}\n")

    # Check for missing candidates
    if len(final_results) != len(candidates):
        print(f"⚠️  WARNING: Missing candidates!")
        print(f"   Input: {len(candidates)}, Output: {len(final_results)}")
        print(f"   Missing: {len(candidates) - len(final_results)}\n")

    # Save Stage 2 results (ONLY Gemini-ranked strong matches)
    stage_2_file = os.path.join(os.path.dirname(__file__), 'output', f"stage_2_results_{len(candidates)}_candidates.json")
    stage_2_data = {
        'query': query,
        'stage': 'Stage 2A: Gemini Ranking (Strong Matches Only)',
        'note': 'This file only contains strong matches processed by Gemini. Partial/no_match candidates are in the combined results file.',
        'time': stage_2_time,
        'gemini_completeness': {
            'input': strong_input_count,
            'output': strong_output_count,
            'missing': strong_input_count - strong_output_count,
            'percentage': (strong_output_count / strong_input_count * 100) if strong_input_count > 0 else 0
        },
        'strong_matches_ranked': [
            {
                'name': c.get('name'),
                'linkedin_url': c.get('linkedin_url'),
                'relevance_score': c.get('relevance_score'),
                'fit_description': c.get('fit_description'),
                'ranking_rationale': c.get('ranking_rationale'),
                'stage_1_confidence': c.get('stage_1_confidence')
            }
            for c in final_results if c.get('match') == 'strong'
        ]
    }

    with open(stage_2_file, 'w') as f:
        json.dump(stage_2_data, f, indent=2)

    print(f"💾 Stage 2 results saved to: {stage_2_file}")

    # Save final combined results
    output_file = os.path.join(os.path.dirname(__file__), 'output', f"two_stage_results_{len(candidates)}_candidates.json")
    output_data = {
        'query': query,
        'sql': search_result['sql'],
        'total_candidates': len(candidates),
        'performance': {
            'total_time': total_time,
            'stage_1_time': stage_1_time,
            'stage_2_time': stage_2_time,
            'candidates_per_second': len(candidates) / pipeline_time
        },
        'costs': costs,
        'distribution': {
            'strong': num_strong,
            'partial': num_partial,
            'no_match': num_no_match
        },
        'ranked_candidates': [
            {
                'name': c.get('name'),
                'linkedin_url': c.get('linkedin_url'),
                'match': c.get('match'),
                'relevance_score': c.get('relevance_score'),
                'fit_description': c.get('fit_description'),
                'ranking_rationale': c.get('ranking_rationale'),
                'stage_1_confidence': c.get('stage_1_confidence')
            }
            for c in final_results
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"💾 Final combined results saved to: {output_file}\n")
    print(f"📊 Summary of saved files:")
    print(f"   • Stage 1: {stage_1_file}")
    print(f"   • Stage 2: {stage_2_file}")
    print(f"   • Combined: {output_file}\n")

    # Display top results by tier
    print("TOP RESULTS BY TIER:")
    print("-" * 80)

    # Strong matches
    strong_results = [c for c in final_results if c.get('match') == 'strong']
    if strong_results:
        print(f"\n🏆 STRONG MATCHES (Top 5 of {len(strong_results)}):")
        for i, c in enumerate(strong_results[:5], 1):
            print(f"\n{i}. {c.get('name')} - Score: {c.get('relevance_score')}")
            print(f"   {c.get('headline')}")
            print(f"   Seniority: {c.get('seniority')} | Location: {c.get('location')}")
            print(f"   Fit: {c.get('fit_description')}")
            print(f"   Rationale: {c.get('ranking_rationale')}")

    # Partial matches
    partial_results = [c for c in final_results if c.get('match') == 'partial']
    if partial_results:
        print(f"\n⚠️  PARTIAL MATCHES (Top 3 of {len(partial_results)}):")
        for i, c in enumerate(partial_results[:3], 1):
            print(f"\n{i}. {c.get('name')} - Score: {c.get('relevance_score')}")
            print(f"   {c.get('headline')}")
            print(f"   Missing: {c.get('fit_description')}")

    print(f"\n{'='*80}\n")

    return {
        'results': final_results,
        'stage_1_results': stage_1_results,
        'performance': {
            'total_time': total_time,
            'stage_1_time': stage_1_time,
            'stage_2_time': stage_2_time,
        },
        'costs': costs
    }


async def compare_with_current(query: str, connected_to: str = 'all', limit: int = 100):
    """
    Compare two-stage pipeline with current ranking_gemini.py
    """
    print(f"\n{'='*80}")
    print(f"COMPARISON TEST: Two-Stage vs Current Gemini")
    print(f"{'='*80}\n")

    # Execute search once
    search_result = execute_search(query, connected_to=connected_to)
    candidates = search_result['results'][:limit]

    print(f"Testing with {len(candidates)} candidates\n")

    # Test current approach
    print("Testing CURRENT approach (ranking_gemini.py)...")
    start_current = time.time()
    current_results = rank_candidates_gemini(query, candidates)
    current_time = time.time() - start_current
    current_cost_estimate = (len(candidates) / 100) * 0.15  # Full profiles

    print(f"✅ Current: {current_time:.2f}s, ~${current_cost_estimate:.4f}")
    print(f"   Ranked: {len(current_results)}/{len(candidates)}")
    if len(current_results) != len(candidates):
        print(f"   ⚠️  Missing: {len(candidates) - len(current_results)} candidates\n")

    # Test two-stage approach
    print("\nTesting NEW two-stage approach...")
    start_new = time.time()
    stage_1_results = await classify_all_candidates(query, candidates)
    final_results, gemini_cost_new = rank_all_candidates(query, stage_1_results)
    new_time = time.time() - start_new
    new_costs = estimate_cost(len(candidates), len(stage_1_results['strong_matches']))

    print(f"✅ New: {new_time:.2f}s, ${new_costs['total_cost']:.4f}")
    print(f"   Ranked: {len(final_results)}/{len(candidates)}")
    if len(final_results) != len(candidates):
        print(f"   ⚠️  Missing: {len(candidates) - len(final_results)} candidates")

    # Check Gemini completeness for new approach (using LinkedIn URLs)
    strong_input_urls = {m['candidate'].get('linkedin_url') for m in stage_1_results['strong_matches']}
    strong_output_results = [r for r in final_results if r.get('match') == 'strong']
    strong_output_urls = {r.get('linkedin_url') for r in strong_output_results}

    missing = strong_input_urls - strong_output_urls
    extra = strong_output_urls - strong_input_urls

    if len(strong_input_urls) > 0:
        completeness_pct = (len(strong_output_urls) / len(strong_input_urls) * 100)
        print(f"   Gemini completeness: {len(strong_output_urls)}/{len(strong_input_urls)} ({completeness_pct:.1f}%)")
        if missing:
            print(f"   ⚠️  Missing {len(missing)} candidates")
        if extra:
            print(f"   ⚠️  Found {len(extra)} extra candidates")
    print()

    # Comparison
    print(f"\n{'='*80}")
    print(f"COMPARISON RESULTS")
    print(f"{'='*80}")
    print(f"Speed:    {'✅ New is faster' if new_time < current_time else '❌ Current is faster'}")
    print(f"          New: {new_time:.2f}s vs Current: {current_time:.2f}s")
    print(f"          Difference: {abs(new_time - current_time):.2f}s ({abs((new_time-current_time)/current_time*100):.1f}%)")

    print(f"\nCost:     {'✅ New is cheaper' if new_costs['total_cost'] < current_cost_estimate else '❌ Current is cheaper'}")
    print(f"          New: ${new_costs['total_cost']:.4f} vs Current: ~${current_cost_estimate:.4f}")
    print(f"          Savings: ${abs(new_costs['total_cost'] - current_cost_estimate):.4f} ({abs((new_costs['total_cost']-current_cost_estimate)/current_cost_estimate*100):.1f}%)")

    print(f"\nCompleteness:")
    print(f"          New: {len(final_results)}/{len(candidates)} ({len(final_results)/len(candidates)*100:.1f}%)")
    print(f"          Current: {len(current_results)}/{len(candidates)} ({len(current_results)/len(candidates)*100:.1f}%)")

    print(f"\nAdditional Benefits of New Approach:")
    print(f"  • Three-tier results: Strong ({len(stage_1_results['strong_matches'])}) / Partial ({len(stage_1_results['partial_matches'])}) / No Match ({len(stage_1_results['no_matches'])})")
    print(f"  • Detailed fit descriptions from GPT-5-nano")
    print(f"  • Confidence scores for classifications")
    print(f"  • Scalable to 1000+ candidates")
    print(f"{'='*80}\n")


# Test scenarios
async def run_all_tests():
    """Run comprehensive test suite"""
    print("\n" + "="*80)
    print("TWO-STAGE RANKING PIPELINE - TEST SUITE")
    print("="*80)

    # Test 1: Small query (~50 candidates)
    print("\n\nTEST 1: Small Query (~50 candidates)")
    await test_two_stage_pipeline(
        query="Find VPs in fintech",
        connected_to='all',
        limit=50
    )

    # Test 2: Medium query (~150 candidates)
    print("\n\nTEST 2: Medium Query (~150 candidates)")
    await test_two_stage_pipeline(
        query="Find directors with startup experience",
        connected_to='all',
        limit=150
    )

    # Test 3: Large query (~300 candidates)
    print("\n\nTEST 3: Large Query (~300 candidates)")
    await test_two_stage_pipeline(
        query="Find senior engineers",
        connected_to='all',
        limit=300
    )

    # Test 4: Comparison with current approach
    print("\n\nTEST 4: Comparison with Current System")
    await compare_with_current(
        query="CEO at healthcare company with startup experience",
        connected_to='all',
        limit=100
    )


if __name__ == "__main__":
    # Run specific test or full suite
    import sys

    if len(sys.argv) > 1:
        # Run specific test with query from command line
        query = ' '.join(sys.argv[1:])
        asyncio.run(test_two_stage_pipeline(query=query, connected_to='all'))
    else:
        # Run full test suite
        asyncio.run(run_all_tests())
