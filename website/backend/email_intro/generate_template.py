"""
Generate AI-powered email templates for candidate introductions via mutual connections

Uses GPT-4o to create professional, personalized introduction emails that:
- Reference the mutual connection
- Highlight candidate's relevant experience
- Clearly state the opportunity/role
- Maintain a professional, formal tone
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

client = OpenAI()


def generate_introduction_email(
    candidate: dict,
    job_description: str,
    mutual_connection_name: str,
    sender_info: dict
):
    """
    Generate a professional introduction email template

    Args:
        candidate: Full candidate profile dict with name, headline, experiences, etc.
        job_description: Description of the role/opportunity
        mutual_connection_name: Name of the mutual connection (e.g., "Linda", "Dan")
        sender_info: Dict with sender's name, company, role, email

    Returns:
        Dict with 'subject' and 'body' (HTML formatted)
    """

    # Extract key candidate information
    candidate_name = candidate.get('name', 'this candidate')
    candidate_headline = candidate.get('headline', '')
    candidate_linkedin_url = candidate.get('linkedin_url', candidate.get('linkedinUrl', ''))
    candidate_experience = candidate.get('experiences', [])

    # Build experience summary (top 2-3 roles)
    experience_summary = []
    for exp in candidate_experience[:3]:
        org = exp.get('org', '')
        title = exp.get('title', '')
        if org and title:
            experience_summary.append(f"{title} at {org}")

    experience_text = '; '.join(experience_summary) if experience_summary else candidate_headline

    # Create prompt for GPT-4o
    prompt = f"""Generate a professional, formal email asking a mutual connection to introduce you to a candidate.

CONTEXT:
- Sender: {sender_info.get('name')} ({sender_info.get('role')} at {sender_info.get('company')})
- Recipient (Mutual Connection): {mutual_connection_name}
- Candidate to be introduced to: {candidate_name}
- Candidate LinkedIn: {candidate_linkedin_url}
- Candidate Background: {experience_text}
- Opportunity: {job_description}

EMAIL PURPOSE:
The sender is reaching out to {mutual_connection_name} (their mutual connection) to ask for an introduction to {candidate_name}. The sender is hiring for a role and believes {candidate_name} would be a great fit.

REQUIREMENTS:
1. Professional and formal tone
2. Address the email to {mutual_connection_name} (the mutual connection)
3. Explain that you're reaching out because they're connected to {candidate_name}
4. Make the candidate's name a hyperlink to their LinkedIn profile: <a href="{candidate_linkedin_url}">{candidate_name}</a>
5. Briefly mention why {candidate_name} caught your attention (2-3 impressive highlights)
6. Explain the opportunity/role you're hiring for (1-2 sentences)
7. Make a clear, polite ask: "Would you be willing to introduce me to {candidate_name}?" or similar
8. Keep email concise (3-4 short paragraphs)
9. End with appropriate professional closing

Generate both:
1. Subject line (e.g., "Introduction Request: [Candidate Name]")
2. Email body (HTML formatted with <p> tags, <br> for line breaks)

EXAMPLE STRUCTURE (DO NOT COPY - generate original content):
{{
    "subject": "Introduction Request: [Candidate Name]",
    "body": "<p>Hi [Connection Name],</p><p>I hope this email finds you well. I noticed you're connected to <a href=\"[LinkedIn URL]\">[Candidate Name]</a>, and I wanted to reach out.</p><p>I'm currently hiring for a [Role] at [Company]. After reviewing [Candidate's] background, I was particularly impressed by [specific highlights - e.g., their experience leading X at Y, their expertise in Z]. Their experience with [relevant skill/domain] would be a strong fit for what we're building.</p><p>Would you be willing to introduce me to <a href=\"[LinkedIn URL]\">[Candidate Name]</a>? I'd love to learn more about their work and explore if there might be mutual interest.</p><p>Best regards,<br>[Your Name]</p>"
}}

Return ONLY valid JSON following this structure with original, personalized content."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at writing professional introduction emails for recruiting and networking. Generate clear, concise, and effective emails."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)

        return {
            'subject': result.get('subject', f'Introduction Request: {candidate_name}'),
            'body': result.get('body', '<p>Error generating email body</p>')
        }

    except Exception as e:
        print(f"Error generating email template: {e}")
        return {
            'subject': f'Introduction Request: {candidate_name}',
            'body': f'<p>Error generating email template: {str(e)}</p>'
        }


