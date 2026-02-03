"""
Supabase configuration and client setup
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv, dotenv_values

# Try to load from environment variables first (Railway)
# Then fallback to .env file (local development)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"[DEBUG supabase_config.py] SUPABASE_URL from env: {SUPABASE_URL is not None}")
print(f"[DEBUG supabase_config.py] SERVICE_KEY from env: {SUPABASE_SERVICE_ROLE_KEY is not None}")

# If not in environment, try loading from .env file
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print(f"[DEBUG supabase_config.py] Trying to load from .env file...")
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    print(f"[DEBUG supabase_config.py] .env path: {env_path}")
    print(f"[DEBUG supabase_config.py] .env exists: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        env_vars = dotenv_values(env_path)
        SUPABASE_URL = SUPABASE_URL or env_vars.get("SUPABASE_URL")
        SUPABASE_SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY or env_vars.get("SUPABASE_SERVICE_ROLE_KEY")
        print(f"[DEBUG supabase_config.py] Loaded from .env - URL: {SUPABASE_URL is not None}, KEY: {SUPABASE_SERVICE_ROLE_KEY is not None}")

def get_supabase_client() -> Client:
    """
    Get Supabase client with service role key for admin operations
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Missing Supabase credentials in .env file")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def test_connection() -> bool:
    """
    Test Supabase connection
    """
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        result = client.table('candidates').select("count", count='exact').limit(0).execute()
        print(f"✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
