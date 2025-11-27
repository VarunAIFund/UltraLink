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
    prompt = f"""Generate a friendly, casual email asking a mutual connection to introduce you to a candidate.

CONTEXT:
- Sender: {sender_info.get('name')} ({sender_info.get('role')} at {sender_info.get('company')})
- Recipient (Mutual Connection): {mutual_connection_name}
- Candidate to be introduced to: {candidate_name}
- Candidate LinkedIn: {candidate_linkedin_url}
- Candidate Background: {experience_text}
- Opportunity: {job_description}

EMAIL PURPOSE:
The sender is reaching out to {mutual_connection_name} (their mutual connection) to ask for an introduction to {candidate_name}. The sender is hiring for a role and believes {candidate_name} would be a great fit. These are colleagues/friends, so the tone should be casual and friendly, not formal.

REQUIREMENTS:
1. Friendly and casual tone (these are colleagues, not strangers)
2. Address the email to {mutual_connection_name} (the mutual connection) - use "Hey" or "Hi"
3. Skip formal greetings like "I hope this email finds you well"
4. Say you noticed they're connected to {candidate_name}
5. Make the candidate's name a hyperlink to their LinkedIn profile ONLY ONCE: <a href="{candidate_linkedin_url}">{candidate_name}</a>
6. Say you're looking for [role] and the candidate's background "seems to be a potential fit" - DO NOT assume they are definitely a fit
7. Mention 2-3 impressive highlights from their background
8. Briefly describe what the opportunity involves (1-2 sentences)
9. ASK FOR THEIR OPINION: "I was wondering if you think [he'd/she'd] be a good fit?"
10. Give them an easy out: "If you do, could you connect me with [Name]? If you don't know [him/her] well enough, would it be ok for me to use your name as a reference if I reach out directly?"
11. Keep email concise (3 short paragraphs)
12. End with casual closing like "Thanks" or "Best Regards"

Generate both:
1. Subject line (e.g., "Introduction Request: [Candidate Name]")
2. Email body (HTML formatted with <p> tags, <br> for line breaks)

EXAMPLE STRUCTURE (DO NOT COPY - generate original content):
{{
    "subject": "Introduction Request: [Candidate Name]",
    "body": "<p>Hey [Connection Name],</p><p>I noticed you're connected to <a href=\"[LinkedIn URL]\">[Candidate Name]</a>. I'm on the lookout for a [Role] for [Company/description], and [his/her] background seems to be a potential fit.</p><p>[Candidate's] experience [highlight 1] and [highlight 2] are particularly impressive. The opportunity involves [brief description], and I was wondering if you think [he'd/she'd] be a good fit? If you do, could you connect me with [Candidate Name]? I'd love to chat with [him/her] about this opportunity. If you don't know [him/her] well enough, would it be ok for me to use your name as a reference if I reach out to [him/her] directly?</p><p>Thanks!<br>[Your Name]</p>"
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


