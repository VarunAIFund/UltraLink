"""
Ranking Stage 1 - Classify candidates as strong or partial matches
"""
import json
import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

client = AsyncOpenAI()

async def classify_single_candidate(query: str, candidate: dict, index: int):
    """Classify a single candidate as strong or partial match"""
    summary = {
        'index': index,
        'name': candidate.get('name'),
        'headline': candidate.get('headline'),
        'seniority': candidate.get('seniority'),
        'location': candidate.get('location'),
        'skills': candidate.get('skills', []),
        'years_experience': candidate.get('years_experience'),
        'worked_at_startup': candidate.get('worked_at_startup'),
        'experiences': candidate.get('experiences'),
        'education': candidate.get('education')
    }

    prompt = f"""Given this search query: "{query}"

Classify this candidate as either "strong" or "partial" match and provide a fit description.

Strong match: Candidate closely matches the query requirements
- fit_description should explain WHY they're a good match (highlight strengths)

Partial match: Candidate has some relevant skills/experience but not a close match
- fit_description should explain:  What they're MISSING from the requirements

Candidate:
{json.dumps(summary, indent=2)}

Respond ONLY with valid JSON:
{{
  "match_type": "strong",
  "fit_description": "Strong CEO background in healthcare with 8 years at health tech startups"
}}
or
{{
  "match_type": "partial",
  "fit_description": "Not CEO or co-founder"
}}
or
{{
  "match_type": "partial",
  "fit_description": "Missing healthcare experience"
}}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
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

        result = json.loads(response_text)
        match_type = result.get('match_type', 'partial')
        fit_description = result.get('fit_description', '')

        # Add fit_description to candidate data
        candidate_with_fit = candidate.copy()
        candidate_with_fit['fit_description'] = fit_description

        return {
            'index': index,
            'match_type': match_type,
            'candidate': candidate_with_fit
        }

    except Exception as e:
        print(f"Classification error for {candidate.get('name', 'Unknown')}: {e}")
        candidate_with_fit = candidate.copy()
        candidate_with_fit['fit_description'] = 'Classification error occurred'
        return {
            'index': index,
            'match_type': 'partial',
            'candidate': candidate_with_fit
        }

async def classify_candidates(query: str, candidates: list):
    """Classify all candidates as strong or partial matches using async parallel calls"""
    if not candidates or len(candidates) == 0:
        return {'strong_matches': [], 'partial_matches': []}

    print(f"Classifying {len(candidates)} candidates in parallel...")

    # Create tasks for all candidates
    tasks = []
    for i, candidate in enumerate(candidates):
        task = asyncio.create_task(classify_single_candidate(query, candidate, i))
        tasks.append(task)

    # Wait for all classifications to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate into strong and partial matches
    strong_matches = []
    partial_matches = []

    for result in results:
        if isinstance(result, Exception):
            print(f"Task failed: {result}")
            continue

        if result['match_type'] == 'strong':
            strong_matches.append(result['candidate'])
        else:
            partial_matches.append(result['candidate'])

    print(f"Classification complete: {len(strong_matches)} strong, {len(partial_matches)} partial")

    return {
        'strong_matches': strong_matches,
        'partial_matches': partial_matches
    }
