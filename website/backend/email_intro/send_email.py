"""
Send emails using Resend API

Handles email delivery for candidate introduction requests via mutual connections.
"""
import os
import resend
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

# Configure Resend API
resend.api_key = os.getenv('RESEND_API_KEY')


def send_introduction_email(
    to_email: str,
    subject: str,
    html_body: str,
    sender_info: dict
):
    """
    Send introduction email via Resend API

    Args:
        to_email: Recipient email address (mutual connection)
        subject: Email subject line
        html_body: HTML formatted email body
        sender_info: Dict with sender's name and email

    Returns:
        Dict with:
        - success: bool
        - message_id: str (if successful)
        - error: str (if failed)
    """

    # Validate inputs
    if not resend.api_key:
        return {
            'success': False,
            'error': 'RESEND_API_KEY not configured in environment variables'
        }

    # Use email only (no display name)
    from_address = sender_info.get('email', 'varun@aifund.ai')

    # Hard-coded recipient (for testing)
    recipient_email = "varun@aifund.ai"

    try:
        # Send email via Resend (always to/from varun@aifund.ai)
        response = resend.Emails.send({
            "from": from_address,
            "to": recipient_email,
            "subject": subject,
            "html": html_body
        })

        return {
            'success': True,
            'message_id': response.get('id', '')
        }

    except Exception as e:
        error_message = str(e)
        print(f"Error sending email: {error_message}")

        return {
            'success': False,
            'error': error_message
        }


