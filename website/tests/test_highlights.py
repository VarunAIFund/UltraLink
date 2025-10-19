"""
Test script for highlights generation
"""
import json
import requests

# Sample candidate data (Shalin Mantri from earlier example)
SAMPLE_CANDIDATE = {
    "name": "Shalin Mantri",
    "headline": "AI product builder; PM leader ex-Uber/ex-Google; startup investor/advisor",
    "location": "Mountain View, California, United States",
    "linkedin_url": "https://www.linkedin.com/in/shalinmantri",
    "seniority": "Director",
    "skills": [
        "mobility",
        "fleet management",
        "location-based services",
        "hardware-software integration",
        "patent development",
        "team leadership"
    ],
    "experiences": [
        {
            "org": "Stealth AI Startup",
            "title": "Founder",
            "summary": "Founder of a stealth AI startup focused on Artificial General Intelligence.",
            "location": "",
            "company_skills": ["ai/AGI", "research and development", "startup leadership"]
        },
        {
            "org": "Google",
            "title": "Director of Product Management",
            "summary": "Led Transportation & Logistics for Geo. Our routing, navigation, and fleet platforms powered millions of trips per day across Google Maps.",
            "location": "San Francisco Bay Area, United States",
            "company_skills": ["routing", "navigation", "fleet management", "maps", "mobile"]
        }
    ],
    "education": [
        {
            "school": "Stanford University",
            "degree": "Master of Science - MS",
            "field": "Management Science & Engineering"
        }
    ]
}

def test_highlights_api():
    """Test the /generate-highlights endpoint"""

    print("=" * 60)
    print("Testing Highlights API")
    print("=" * 60)

    print(f"\nCandidate: {SAMPLE_CANDIDATE['name']}")
    print(f"Headline: {SAMPLE_CANDIDATE['headline']}")
    print(f"Current role: {SAMPLE_CANDIDATE['experiences'][0]['title']} at {SAMPLE_CANDIDATE['experiences'][0]['org']}")

    print("\n" + "-" * 60)
    print("Sending request to http://localhost:5000/generate-highlights")
    print("-" * 60)

    try:
        response = requests.post(
            'http://localhost:5000/generate-highlights',
            json={'candidate': SAMPLE_CANDIDATE},
            headers={'Content-Type': 'application/json'},
            timeout=60  # Perplexity can take a bit longer
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print(f"\n✅ Success!")
            print(f"Total sources: {data.get('total_sources', 0)}")
            print(f"Number of highlights: {len(data.get('highlights', []))}")

            print("\n" + "=" * 60)
            print("HIGHLIGHTS:")
            print("=" * 60)

            for i, highlight in enumerate(data.get('highlights', []), 1):
                print(f"\n[{i}] {highlight['text']}")
                print(f"    📎 Source: {highlight['source']}")
                print(f"    🔗 URL: {highlight['url']}")

            # Save to file for inspection
            with open('test_highlights_output.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\n" + "=" * 60)
            print("✅ Full response saved to: test_highlights_output.json")
            print("=" * 60)

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask server")
        print("Make sure the server is running: python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

if __name__ == '__main__':
    test_highlights_api()
