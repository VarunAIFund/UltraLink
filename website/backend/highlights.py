"""
Highlights module - Perplexity-powered professional insights generation
"""
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Perplexity client
perplexity = OpenAI(
    api_key=os.getenv('PERPLEXITY_API_KEY'),
    base_url="https://api.perplexity.ai"
)

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

def generate_highlights(candidate):
    """
    Generate detailed professional highlights with source citations using Perplexity

    Args:
        candidate: Dict with candidate data (name, headline, location, linkedin_url, experiences, skills)

    Returns:
        Dict with 'highlights' (list of {text, source, url}) and 'total_sources' (int)
    """
    name = candidate.get('name')
    headline = candidate.get('headline', '')
    linkedin_url = candidate.get('linkedin_url')
    location = candidate.get('location', '')

    # Extract current role from first experience
    experiences = candidate.get('experiences', [])
    current_exp = experiences[0] if experiences else {}
    current_company = current_exp.get('org', '')
    current_title = current_exp.get('title', '')

    # Get top skills
    skills = candidate.get('skills', [])[:5]
    skills_str = ', '.join(skills) if skills else 'various technical skills'

    prompt = f"""Search the web for professional information about {name}.

Profile context:
- Current role: {current_title} at {current_company}
- Location: {location}
- Headline: {headline}
- Key skills: {skills_str}
- LinkedIn: {linkedin_url}

Provide 5-7 detailed insights about their professional background. Each insight should:
- Be 2-3 sentences describing a specific aspect (current role, tech stack, projects, education, achievements, speaking engagements, publications)
- Include specific technical details, companies, technologies, or accomplishments
- Be based on verifiable web sources
- Focus on different aspects of their career

Write each insight as a separate paragraph. Write in third person."""

    try:
        response = perplexity.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": "You are a professional recruiter. Provide detailed, factual insights with specific examples."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content

        # Perplexity returns citations in the response object
        citations = []
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations
        # Check message for citations as well
        elif hasattr(response.choices[0].message, 'citations'):
            citations = response.choices[0].message.citations

        print(f"[DEBUG] Generated {len(content.split(chr(10)+chr(10)))} paragraphs")
        print(f"[DEBUG] Found {len(citations)} citations")

        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Create highlight blocks - map each paragraph to a citation
        highlights = []
        for i, paragraph in enumerate(paragraphs):
            # Cycle through citations if we have fewer citations than paragraphs
            citation_url = citations[i % len(citations)] if citations else None

            # Extract domain for display
            source_display = extract_domain(citation_url) if citation_url else "Unknown source"

            highlights.append({
                'text': paragraph,
                'source': source_display,
                'url': citation_url
            })

        return {
            'highlights': highlights,
            'total_sources': len(set(citations)) if citations else 0
        }

    except Exception as e:
        print(f"[ERROR] Perplexity API error: {e}")
        raise
