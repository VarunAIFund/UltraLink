"""
Ranking Stage 2 - Gemini Ranking of Pre-Classified Candidates
Takes output from Stage 1 (GPT-5-nano classifications) and ranks with Gemini
"""
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from constants import RANKING_STAGE_2_MODEL

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel(RANKING_STAGE_2_MODEL)


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


def rank_strong_matches_with_gemini(query: str, strong_matches: list):
    """
    Rank strong matches using Gemini with compressed summaries

    Args:
        query: The search query
        strong_matches: List of dicts with {candidate, analysis, match_type, confidence}

    Returns:
        List of ranked candidates with relevance_score and ranking_rationale
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

    print(f"\n🎯 Stage 2A: Ranking {len(strong_matches)} strong matches with Gemini...")

    # Create compressed summaries (name + GPT-5-nano analysis only)
    # This is WAY smaller than full profiles: ~300 tokens vs ~2000 tokens each
    summaries = []
    for i, match in enumerate(strong_matches):
        candidate = match['candidate']
        summaries.append({
            'index': i,
            'name': candidate.get('name'),
            'analysis': match['analysis']  # The "why strong" from GPT-5-nano
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
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'response_mime_type': 'application/json'
            }
        )

        response_text = response.text.strip()

        # Track token usage and cost
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            total_tokens = usage_metadata.total_token_count

            # Gemini 2.5 Pro pricing (tiered by context length)
            # < 200K tokens: $1.25/M input, $10/M output
            # > 200K tokens: $2.50/M input, $15/M output
            if input_tokens <= 200_000:
                cost_input = (input_tokens / 1_000_000) * 1.25
                cost_output = (output_tokens / 1_000_000) * 10.00
            else:
                cost_input = (input_tokens / 1_000_000) * 2.50
                cost_output = (output_tokens / 1_000_000) * 15.00

            total_cost = cost_input + cost_output

            print(f"\n💰 Gemini Ranking Cost:")
            print(f"   • Input tokens: {input_tokens:,} (${cost_input:.4f})")
            print(f"   • Output tokens: {output_tokens:,} (${cost_output:.4f})")
            print(f"   • Total tokens: {total_tokens:,}")
            print(f"   • Total cost: ${total_cost:.4f}")

            # Store cost data for return
            gemini_cost = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost_input': cost_input,
                'cost_output': cost_output,
                'total_cost': total_cost
            }
        else:
            # No token data available
            gemini_cost = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost_input': 0.0,
                'cost_output': 0.0,
                'total_cost': 0.0
            }

        # Extract JSON
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        ranking_data = json.loads(response_text)

        # Map rankings back to full candidates
        ranked_indices = set()
        ranked_results = []

        for ranked_item in ranking_data['ranked_candidates']:
            original_index = ranked_item['index']
            if 0 <= original_index < len(strong_matches):
                ranked_indices.add(original_index)

                match = strong_matches[original_index]
                candidate = match['candidate'].copy()

                # Add Stage 1 data
                candidate['match'] = 'strong'
                candidate['fit_description'] = match['analysis']  # GPT-5-nano's "why strong"
                candidate['stage_1_confidence'] = match['confidence']

                # Add Stage 2 data
                candidate['relevance_score'] = ranked_item.get('relevance_score', 50)
                # ranking_rationale removed to save tokens (not displayed in UI)

                ranked_results.append(candidate)

        # Check for missing candidates
        missing_indices = set(range(len(strong_matches))) - ranked_indices
        if missing_indices:
            missing_names = [strong_matches[i]['candidate'].get('name', 'Unknown') for i in sorted(missing_indices)]
            print(f"⚠️  Warning: Gemini skipped {len(missing_indices)} candidates: {missing_names}")
            print(f"   Indices: {sorted(missing_indices)}")

            # Add missing candidates at the end with lower scores
            for idx in sorted(missing_indices):
                match = strong_matches[idx]
                candidate = match['candidate'].copy()
                candidate['match'] = 'strong'
                candidate['fit_description'] = match['analysis']
                candidate['stage_1_confidence'] = match['confidence']
                candidate['relevance_score'] = 80  # Lower score for skipped
                # ranking_rationale removed to save tokens
                ranked_results.append(candidate)

        print(f"✅ Stage 2A Complete: {len(ranked_results)} strong matches ranked")
        return ranked_results, gemini_cost

    except Exception as e:
        print(f"❌ Gemini ranking error: {e}")
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
            # ranking_rationale removed to save tokens
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


def rank_all_candidates(query: str, stage_1_results: dict):
    """
    Complete Stage 2 ranking pipeline

    Args:
        query: The search query
        stage_1_results: Dict from Stage 1 with strong_matches, partial_matches, no_matches

    Returns:
        List of all ranked candidates (strong → partial → no_match tiers)
    """
    print(f"\n{'='*60}")
    print(f"STAGE 2: RANKING & SCORING")
    print(f"{'='*60}")

    # Rank strong matches with Gemini (compressed summaries)
    strong_ranked, gemini_cost = rank_strong_matches_with_gemini(
        query,
        stage_1_results['strong_matches']
    )

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
    print(f"  • Strong matches: {len(strong_ranked)} (Gemini ranked)")
    print(f"  • Partial matches: {len(partial_scored)} (Rule scored)")
    print(f"  • No matches: {len(no_match_list)} (Filtered)")
    print(f"{'='*60}\n")

    return final_results, gemini_cost


# Test function
def test_ranking():
    """Test Stage 2 with sample Stage 1 output"""
    # Simulate Stage 1 output
    stage_1_results = {
        'strong_matches': [
            {
                'index': 0,
                'match_type': 'strong',
                'analysis': 'VP Engineering at Stripe with 15 years experience. Strong match because: extensive fintech leadership, built B2B SaaS platforms, Stanford CS degree, led ML initiatives.',
                'confidence': 95,
                'candidate': {
                    'name': 'Jane Smith',
                    'headline': 'VP Engineering at Stripe',
                    'seniority': 'VP',
                    'skills': ['Python', 'Leadership', 'AWS'],
                    'years_experience': 15,
                    'worked_at_startup': True
                }
            },
            {
                'index': 1,
                'match_type': 'strong',
                'analysis': 'Director of Engineering at Square with 12 years experience. Strong because: fintech background, scaling experience, MIT graduate.',
                'confidence': 88,
                'candidate': {
                    'name': 'John Doe',
                    'headline': 'Director Engineering at Square',
                    'seniority': 'Director',
                    'skills': ['Java', 'Leadership', 'Scala'],
                    'years_experience': 12,
                    'worked_at_startup': True
                }
            }
        ],
        'partial_matches': [
            {
                'index': 2,
                'match_type': 'partial',
                'analysis': 'Missing fintech experience - background is in e-commerce',
                'confidence': 60,
                'candidate': {
                    'name': 'Alice Johnson',
                    'headline': 'Senior Engineer at Amazon',
                    'seniority': 'Senior',
                    'skills': ['Python', 'AWS'],
                    'years_experience': 8,
                    'worked_at_startup': False
                }
            }
        ],
        'no_matches': []
    }

    query = "Find VPs in fintech with startup experience"
    results = rank_all_candidates(query, stage_1_results)

    print("\n--- Test Results ---")
    for r in results:
        print(f"\n{r['name']} ({r['match']})")
        print(f"  Score: {r['relevance_score']}")
        print(f"  Fit: {r['fit_description']}")
        print(f"  Rationale: {r['ranking_rationale']}")


if __name__ == "__main__":
    test_ranking()
