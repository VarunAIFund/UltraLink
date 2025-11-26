"""
Test email generation for candidate introductions via mutual connections
"""
import sys
import os
import json

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import from email_intro module
from email_intro.generate_template import generate_introduction_email


def test_email_generation():
    """Test generating an introduction email"""

    # Sample candidate data
    test_candidate = {
        'name': 'Jane Smith',
        'headline': 'VP Engineering at Stripe',
        'linkedin_url': 'https://www.linkedin.com/in/janesmith',
        'location': 'San Francisco, CA',
        'seniority': 'VP',
        'years_experience': 15,
        'skills': ['Python', 'Leadership', 'AWS', 'ML'],
        'experiences': [
            {
                'org': 'Stripe',
                'title': 'VP Engineering',
                'summary': 'Led engineering teams across payments infrastructure',
                'location': 'San Francisco, CA'
            },
            {
                'org': 'Square',
                'title': 'Director of Engineering',
                'summary': 'Built and scaled seller platform engineering team',
                'location': 'San Francisco, CA'
            },
            {
                'org': 'Google',
                'title': 'Senior Engineering Manager',
                'summary': 'Managed Cloud Platform engineering teams',
                'location': 'Mountain View, CA'
            }
        ],
        'education': [
            {
                'school': 'Stanford University',
                'degree': 'BS',
                'field': 'Computer Science'
            }
        ]
    }

    # Job description
    test_job_desc = """VP of Engineering at a well-funded Series B fintech startup (raised $50M).
    Leading a team of 30+ engineers building next-generation payment infrastructure for B2B SaaS companies.
    Looking for someone with experience scaling engineering teams, payments/fintech domain expertise,
    and a track record of building reliable, high-throughput systems."""

    # Mutual connection
    test_connection = "Linda"

    # Sender info
    test_sender = {
        'name': 'John Doe',
        'role': 'CEO',
        'company': 'PaymentFlow',
        'email': 'john@paymentflow.com'
    }

    print("=" * 80)
    print("TEST: Email Generation for Candidate Introduction")
    print("=" * 80)
    print(f"\nCandidate: {test_candidate['name']}")
    print(f"Mutual Connection: {test_connection}")
    print(f"Sender: {test_sender['name']} ({test_sender['role']} at {test_sender['company']})")
    print(f"\nJob Description:\n{test_job_desc}")
    print("\n" + "=" * 80)
    print("GENERATING EMAIL...")
    print("=" * 80 + "\n")

    # Generate email
    result = generate_introduction_email(
        candidate=test_candidate,
        job_description=test_job_desc,
        mutual_connection_name=test_connection,
        sender_info=test_sender
    )

    # Display results
    print("\n" + "=" * 80)
    print("GENERATED EMAIL")
    print("=" * 80)
    print(f"\nSUBJECT:\n{result['subject']}")
    print(f"\nBODY (HTML):\n{result['body']}")
    print("\n" + "=" * 80)

    # Save to JSON file
    output_file = os.path.join(os.path.dirname(__file__), 'output', 'test_email_generation.json')
    output_data = {
        'test_case': {
            'candidate_name': test_candidate['name'],
            'mutual_connection': test_connection,
            'sender': test_sender,
            'job_description': test_job_desc
        },
        'generated_email': {
            'subject': result['subject'],
            'body': result['body']
        }
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == "__main__":
    test_email_generation()
