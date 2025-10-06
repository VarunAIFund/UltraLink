"""
Supabase configuration and client setup
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv, dotenv_values

# Load environment variables from parent directory using dotenv_values to avoid env var conflicts
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
env_vars = dotenv_values(env_path)

# Get Supabase credentials from the .env file directly
SUPABASE_URL = env_vars.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = env_vars.get("SUPABASE_SERVICE_ROLE_KEY")

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
