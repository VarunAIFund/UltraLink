"""
Ranking module - Gemini powered candidate ranking with larger context window
"""
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-pro')

def rank_candidates_gemini(query: str, candidates: list):
    """Rank ALL candidates using Gemini's large context window"""
    if not candidates or len(candidates) == 0:
        return candidates

    # No limit - use all candidates (Gemini has 2M token context window)
    candidates_to_rank = candidates

    # Prepare summaries
    summaries = []
    for i, candidate in enumerate(candidates_to_rank):
        summaries.append({
            'index': i,
            'name': candidate.get('name'),
            'headline': candidate.get('headline'),
            'seniority': candidate.get('seniority'),
            'location': candidate.get('location'),
            'skills': candidate.get('skills', []),
            'years_experience': candidate.get('years_experience'),
            'worked_at_startup': candidate.get('worked_at_startup'),
            'experiences': candidate.get('experiences'),
            'education': candidate.get('education')
        })

    print(f"Ranking {len(summaries)} candidates with Gemini...")

    prompt = f"""Given this search query: "{query}"

Analyze these {len(summaries)} candidates and:
1. Rank them by relevance (most relevant first)
2. IMPORTANT: You MUST rank ALL {len(summaries)} candidates - do not skip any
3. For each candidate, provide:
- relevance_score (0-100)
- fit_description (1-2 sentences why they're a good fit)

Candidates:
{json.dumps(summaries, indent=2)}

Respond ONLY with valid JSON:
{{
  "ranked_candidates": [
    {{
      "index": 0,
      "relevance_score": 95,
      "fit_description": "..."
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

        # Track token usage and cost (safely)
        print("[DEBUG] Attempting to track Gemini tokens...")
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage_metadata = response.usage_metadata
                input_tokens = getattr(usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(usage_metadata, 'candidates_token_count', 0)
                total_tokens = getattr(usage_metadata, 'total_token_count', 0)

                if total_tokens > 0:
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
        except Exception as e:
            print(f"[DEBUG] Could not track Gemini tokens: {e}")

        # Extract JSON
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        ranking_data = json.loads(response_text)

        # Reorder candidates
        ranked_results = []
        for ranked_item in ranking_data['ranked_candidates']:
            original_index = ranked_item['index']
            if 0 <= original_index < len(candidates_to_rank):
                candidate = candidates_to_rank[original_index].copy()
                candidate['relevance_score'] = ranked_item.get('relevance_score', 50)
                candidate['fit_description'] = ranked_item.get('fit_description', '')
                ranked_results.append(candidate)

        print(f"Gemini ranking complete: {len(ranked_results)} candidates ranked")
        return ranked_results

    except Exception as e:
        print(f"Gemini ranking error: {e}")
        import traceback
        traceback.print_exc()
        return candidates
