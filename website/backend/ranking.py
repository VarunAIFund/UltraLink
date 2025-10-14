"""
Ranking module - GPT-4o powered candidate ranking
"""
import json
from openai import OpenAI

client = OpenAI()

def rank_candidates(query: str, candidates: list):
    """Rank candidates using GPT-4o"""
    if not candidates or len(candidates) == 0:
        return candidates

    # Limit to top 30 to avoid token limits
    candidates_to_rank = candidates[:30]
    remaining = candidates[30:]

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
            'connected_to': candidate.get('connected_to', []),
            'experiences': candidate.get('experiences'),
            'education': candidate.get('education')
        })

    prompt = f"""Given this search query: "{query}"

Analyze these {len(summaries)} candidates and:
1. Rank them by relevance (most relevant first)
2. For each, provide:
   - relevance_score (0-100)
   - fit_description (1-2 sentences why they're a good fit)
   - ranking_insight (why they got this score/rank)

Candidates:
{json.dumps(summaries, indent=2)}

Respond ONLY with valid JSON:
{{
  "ranked_candidates": [
    {{
      "index": 0,
      "relevance_score": 95,
      "fit_description": "...",
      "ranking_insight": "..."
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a recruiting expert. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        response_text = response.choices[0].message.content.strip()

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
                candidate['ranking_insight'] = ranked_item.get('ranking_insight', '')
                ranked_results.append(candidate)

        # Append unranked candidates
        ranked_results.extend(remaining)

        return ranked_results

    except Exception as e:
        print(f"Ranking error: {e}")
        return candidates
