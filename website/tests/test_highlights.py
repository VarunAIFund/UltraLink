"""
Test script for highlights generation
"""
import json
import requests

# Sample candidate data (Joanna Strober - testing with known prestigious awards)
SAMPLE_CANDIDATE =  {
    "name": "Joanna Strober",
    "linkedinUrl": "https://www.linkedin.com/in/joannastrober",
    "headline": "Founder of Midi Health I TIME100 Health 2025 & CNBC Changemaker 2025 & Forbes 50 Over 50",
    "location": "Los Altos, California, United States",
    "phone": "16509548683",
    "connected_to": [
      "linda"
    ],
    "profilePic": "https://media.licdn.com/dms/image/v2/D5603AQH4sBteUuGB6w/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1719699160838?e=1761782400&v=beta&t=4Vi-9liXbn6eJb7X7uDkEKcL7x01e-5gO5i9y-_1KNc",
    "profilePicHighQuality": "https://media.licdn.com/dms/image/v2/D5603AQH4sBteUuGB6w/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1719699160842?e=1761782400&v=beta&t=UQ9rlGNBu8mIDRIq5gmipSV6fxSc9GVaxvICKlkAK7E",
    "seniority": "C-Level",
    "skills": [
      "digital health",
      "telemedicine",
      "women's health",
      "health insurance",
      "care coordination"
    ],
    "years_experience": 21,
    "average_tenure": 4.2,
    "worked_at_startup": True,
    "experiences": [
      {
        "org": "Midi Health",
        "company_url": "https://www.linkedin.com/company/78749228/",
        "title": "Founder",
        "summary": "Midi Health is building a virtual healthcare platform specifically for women in midlife. Our care is designed by world-class experts, delivered by compassionate clinicians, and covered by insurance.",
        "short_summary": "Founder leading a virtual, insurance-covered midlife healthcare platform for women.",
        "location": "",
        "company_skills": [
          "digital health",
          "telemedicine",
          "women's health",
          "health insurance",
          "care coordination"
        ],
        "business_model": "B2C",
        "product_type": "Platform",
        "industry_tags": [
          "healthcare",
          "digital health",
          "women's health",
          "telemedicine"
        ]
      },
      {
        "org": "WW (formerly Weight Watchers)",
        "company_url": "https://www.linkedin.com/company/7428/",
        "title": "SVP, Kurbo",
        "summary": "Ran Kurbo by WW, the family division at WW. Introduced a new, WW-branded Kurbo mobile app and website and added strategic partnerships to grow adoption and increase revenue.",
        "short_summary": "Led Kurbo within WW, launching branded app and strategic partnerships.",
        "location": "United States",
        "company_skills": [
          "digital health",
          "partnerships",
          "strategic alliances",
          "business strategy"
        ],
        "business_model": "B2C",
        "product_type": "Mobile App",
        "industry_tags": [
          "healthcare",
          "digital health",
          "wellness"
        ]
      },
      {
        "org": "Kurbo Health",
        "company_url": "https://www.linkedin.com/search/results/all/?keywords=Kurbo+Health",
        "title": "Founder and CEO",
        "summary": "Founding CEO for Kurbo Health, the first digital therapeutic addressing childhood obesity. Sold the company with a successful outcome to WW (Weight Watchers) in 2018.",
        "short_summary": "Founded Kurbo Health, first digital therapeutic for childhood obesity, sold to WW in 2018.",
        "location": "Los Altos, California",
        "company_skills": [
          "digital health",
          "pediatric obesity",
          "digital therapeutics"
        ],
        "business_model": "B2C",
        "product_type": "Platform",
        "industry_tags": [
          "healthcare",
          "digital health",
          "pediatrics"
        ]
      }
    ],
    "education": [
      {
        "school": "University of Pennsylvania",
        "degree": "BA",
        "field": "Political Science"
      },
      {
        "school": "University of California, Los Angeles - School of Law",
        "degree": "JD",
        "field": "Law"
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
            import os
            output_file = os.path.join(os.path.dirname(__file__), 'output', 'test_highlights_output.json')
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print("\n" + "=" * 60)
            print(f"✅ Full response saved to: {output_file}")
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
