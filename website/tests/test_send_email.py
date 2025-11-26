"""
Test sending introduction email via Resend API

This will send a real test email to varun@aifund.ai
"""
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from email_intro.send_email import send_introduction_email


def test_send_email():
    """Test sending an introduction email"""

    # Sample email content
    test_subject = "Test: Introduction Request - Jane Smith"

    test_body = """<p>Hi Linda,</p>
<p>I hope this email finds you well. I noticed you're connected to <a href="https://www.linkedin.com/in/janesmith">Jane Smith</a>, and I wanted to reach out.</p>
<p>I'm currently hiring for a VP of Engineering role at a well-funded Series B fintech startup. After reviewing Jane's background, I was particularly impressed by her experience scaling engineering teams at Stripe and Square, and her deep expertise in payments infrastructure. Her track record of building reliable, high-throughput systems would be a strong fit for what we're building.</p>
<p>Would you be willing to introduce me to <a href="https://www.linkedin.com/in/janesmith">Jane Smith</a>? I'd love to learn more about her work and explore if there might be mutual interest.</p>
<p>Best regards,<br>Varun Sharma<br>AI Fund</p>"""

    # Sender info (note: these will be ignored since we hard-coded varun@aifund.ai)
    test_sender = {
        'name': 'Varun Sharma',
        'email': 'varun@aifund.ai'
    }

    print("=" * 80)
    print("TEST: Sending Introduction Email via Resend")
    print("=" * 80)
    print(f"\nFrom: varun@aifund.ai (hard-coded)")
    print(f"To: varun@aifund.ai (hard-coded)")
    print(f"\nSubject: {test_subject}")
    print(f"\nBody Preview:\n{test_body[:200]}...")
    print("\n" + "=" * 80)
    print("SENDING EMAIL...")
    print("=" * 80 + "\n")

    # Send email
    result = send_introduction_email(
        to_email="linda@example.com",  # This will be ignored
        subject=test_subject,
        html_body=test_body,
        sender_info=test_sender  # This will be ignored
    )

    # Display results
    print("\n" + "=" * 80)
    print("SEND RESULT")
    print("=" * 80)

    if result['success']:
        print(f"\n✅ Email sent successfully!")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"\n   Check your inbox at varun@aifund.ai")
    else:
        print(f"\n❌ Email sending failed!")
        print(f"   Error: {result.get('error')}")
        print(f"\n   Make sure:")
        print(f"   1. RESEND_API_KEY is set in .env")
        print(f"   2. varun@aifund.ai is verified in your Resend account")
        print(f"   3. You have Resend package installed: pip install resend")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_send_email()
