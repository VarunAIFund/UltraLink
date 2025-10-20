
from perplexity import Perplexity
import os
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Perplexity client
perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
perplexity = Perplexity(api_key=perplexity_api_key)

search = perplexity.search.create(
    query="Research Joanna Strober's professional background.  Profile: - Current role: Founder at Midi Health - Location: Los Altos, California, United States - Headline: Founder of Midi Health I TIME100 Health 2025 & CNBC Changemaker 2025 & Forbes 50 Over 50  Find ",
    max_results=20,
    max_tokens_per_page=2048
)

# Collect results
search_results = []
for result in search.results:
    print(f"{result.title}: {result.url}")
    search_results.append(result.__dict__)

# Save to JSON
output_file = os.path.join(os.path.dirname(__file__), 'search_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({"results": search_results}, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(search_results)} results to {output_file}")
