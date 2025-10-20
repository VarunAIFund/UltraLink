"""
Highlights module - Two-stage: Perplexity search + GPT analysis
"""
import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
from perplexity import Perplexity

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize clients
perplexity = Perplexity(api_key=os.getenv('PERPLEXITY_API_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_domain(url):
    """Extract clean domain from URL for display"""
    if not url:
        return "Unknown source"

    # Remove protocol
    domain = re.sub(r'^https?://', '', url)
    # Remove www.
    domain = re.sub(r'^www\.', '', domain)
    # Take just the domain (remove path)
    domain = domain.split('/')[0]

    return domain

def search_perplexity(name, current_title, current_company, location, headline):
    """Search Perplexity for sources about the candidate"""
    print(f"[DEBUG] Searching Perplexity for {name}...")

    search_query = f"Research {name}'s professional background. Current role: {current_title} at {current_company}. Location: {location}. Headline: {headline}"

    search = perplexity.search.create(
        query=search_query,
        max_results=20,
        max_tokens_per_page=2048
    )

    # Collect search results
    search_results = []
    for result in search.results:
        search_results.append(result.__dict__)

    print(f"[DEBUG] Found {len(search_results)} sources from Perplexity")
    return search_results

def analyze_with_gpt(name, current_title, current_company, location, search_results):
    """Analyze search results with GPT to create summaries"""
    print(f"[DEBUG] Analyzing with GPT-4o...")

    urls_list = "\n".join([f"- {r.get('title', 'No title')}: {r.get('url', '')}" for r in search_results])

    json_schema = {
        "name": "professional_highlights",
        "schema": {
            "type": "object",
            "properties": {
                "summaries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "url": {"type": "string"},
                            "summary": {"type": "string"}
                        },
                        "required": ["source", "url", "summary"]
                    }
                }
            },
            "required": ["summaries"]
        }
    }

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a professional recruiter analyzing articles about a candidate. For each source, extract the SPECIFIC facts, details, and information from that article. Do not write generic summaries - focus on what makes each source unique and what specific information it provides."
            },
            {
                "role": "user",
                "content": f"""Analyze these sources about {name}:

{urls_list}

Profile: {current_title} at {current_company}, {location}

For each source, create a summary that extracts SPECIFIC information from that article.

CRITICAL RANKING ORDER (most important first):
1. Major awards and recognitions (TIME100, Forbes, CNBC Changemaker, etc.)
2. Major media publications (Business Insider, Oprah Daily, major news outlets)
3. Funding announcements and investor news
4. Podcast interviews and speaking engagements
5. Institutional profiles (universities, research institutes)
6. Company websites and generic profiles (lowest priority)

Include all sources."""
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": json_schema
        }
    )

    data = json.loads(response.choices[0].message.content)
    summaries = data.get('summaries', [])
    print(f"[DEBUG] Generated {len(summaries)} summaries from GPT")

    return summaries

def generate_highlights(candidate):
    """
    Generate detailed professional highlights with source citations

    Args:
        candidate: Dict with candidate data (name, headline, location, linkedin_url, experiences, skills)

    Returns:
        Dict with 'highlights' (list of {text, source, url}) and 'total_sources' (int)
    """
    name = candidate.get('name')
    headline = candidate.get('headline', '')
    location = candidate.get('location', '')

    # Extract current role from first experience
    experiences = candidate.get('experiences', [])
    current_exp = experiences[0] if experiences else {}
    current_company = current_exp.get('org', '')
    current_title = current_exp.get('title', '')

    try:
        # Step 1: Search Perplexity
        search_results = search_perplexity(name, current_title, current_company, location, headline)

        # Step 2: Analyze with GPT
        summaries = analyze_with_gpt(name, current_title, current_company, location, search_results)

        # Transform to frontend format
        highlights = []
        for summary in summaries:
            url = summary.get('url', '')
            highlights.append({
                'text': summary.get('summary', ''),
                'source': extract_domain(url),
                'url': url
            })

        return {
            'highlights': highlights,
            'total_sources': len(highlights)
        }

    except Exception as e:
        print(f"[ERROR] API error: {e}")
        raise
