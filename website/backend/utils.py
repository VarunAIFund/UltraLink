"""
Utility functions for backend
"""
import os
from urllib.parse import urlparse
from dotenv import load_dotenv, dotenv_values

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

# Detect if running on Railway (Railway sets RAILWAY_ENVIRONMENT_NAME)
is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None

if is_railway:
    # Railway: Use os.getenv() which reads from Railway environment variables
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    print(f"[DEBUG utils.py] Railway detected - Using Railway env vars")
else:
    # Local: Use dotenv_values() to read directly from .env file
    if 'SUPABASE_URL' in os.environ:
        del os.environ['SUPABASE_URL']
    load_dotenv(env_path, override=True)
    env_vars = dotenv_values(env_path)
    SUPABASE_URL = env_vars.get('SUPABASE_URL', '')
    print(f"[DEBUG utils.py] Local detected - Using .env file")

BUCKET_NAME = 'profile-pictures'
print(f"[DEBUG utils.py] SUPABASE_URL loaded: {SUPABASE_URL}")

def sanitize_linkedin_url_to_filename(linkedin_url: str) -> str:
    """
    Convert LinkedIn URL to filename format used in storage.

    Example:
        https://www.linkedin.com/in/johndoe/ -> in-johndoe.jpg
        https://linkedin.com/in/jane-smith-123 -> in-jane-smith-123.jpg
    """
    if not linkedin_url:
        return None

    try:
        # Parse URL
        parsed = urlparse(linkedin_url)
        path = parsed.path.strip('/')

        # Extract username (last part after /in/)
        if '/in/' in path:
            username = path.split('/in/')[-1]
        else:
            # Fallback: use entire path
            username = path.replace('/', '-')

        # Clean filename
        username = username.replace('/', '-').replace('?', '').replace('&', '')

        # Construct filename
        filename = f"in-{username}.jpg" if not username.startswith('in-') else f"{username}.jpg"

        return filename
    except Exception:
        return None

def generate_profile_pic_url(linkedin_url: str) -> str:
    """
    Generate Supabase Storage URL from LinkedIn profile URL.

    Args:
        linkedin_url: LinkedIn profile URL (e.g., https://linkedin.com/in/johndoe)

    Returns:
        Supabase Storage URL or None if invalid/default

    Example:
        generate_profile_pic_url("https://linkedin.com/in/johndoe")
        -> "https://[project].supabase.co/storage/v1/object/public/profile-pictures/in-johndoe.jpg"
    """
    if not linkedin_url or not SUPABASE_URL:
        return None

    filename = sanitize_linkedin_url_to_filename(linkedin_url)

    if not filename:
        return None

    # Don't return URL for default.jpg - let frontend show fallback UI
    if filename == 'default.jpg':
        return None

    # Construct Supabase Storage URL
    base_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}"
    profile_pic_url = f"{base_url}/{filename}"

    return profile_pic_url

def add_profile_pic_urls(candidates: list) -> list:
    """
    Add profile_pic URLs to list of candidate dictionaries.

    Args:
        candidates: List of candidate dictionaries with linkedin_url field

    Returns:
        Same list with profile_pic field added/updated
    """
    for candidate in candidates:
        linkedin_url = candidate.get('linkedin_url')

        if linkedin_url:
            profile_pic_url = generate_profile_pic_url(linkedin_url)
            candidate['profile_pic'] = profile_pic_url
        else:
            candidate['profile_pic'] = None

    return candidates
