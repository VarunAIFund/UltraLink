"""
Add and update notes for candidates in the database
"""
import psycopg2
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

def get_db_connection():
    """Get Supabase database connection - always uses connection pooler (port 6543)"""
    # Try Railway environment variables first, fall back to .env file
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')

    if not db_password or not supabase_url:
        # Fall back to .env file for local development
        env_vars = dotenv_values(env_path)
        db_password = env_vars.get('SUPABASE_DB_PASSWORD')
        supabase_url = env_vars.get('SUPABASE_URL', '')

    if not db_password:
        raise ValueError("SUPABASE_DB_PASSWORD environment variable is not set")
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")

    # Extract project ID from Supabase URL
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    encoded_password = quote_plus(db_password)

    # Always use connection pooler (port 6543) for better performance and stability
    conn_string = f"postgresql://postgres.{project_id}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
    print(f"[DEBUG] Using pooler: postgresql://postgres.{project_id}:****@aws-1-us-east-2.pooler.supabase.com:6543/postgres")

    return psycopg2.connect(conn_string)

def update_candidate_note(linkedin_url, note):
    """
    Update or add a note for a candidate

    Args:
        linkedin_url: LinkedIn URL of the candidate (primary key)
        note: Note text to add/update

    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE candidates
            SET notes = %s
            WHERE linkedin_url = %s
        """, (note, linkedin_url))

        rows_updated = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return rows_updated > 0

    except Exception as e:
        print(f"Error updating note: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

def get_candidate_note(linkedin_url):
    """
    Get the current note for a candidate

    Args:
        linkedin_url: LinkedIn URL of the candidate

    Returns:
        Note text or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT notes
            FROM candidates
            WHERE linkedin_url = %s
        """, (linkedin_url,))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return result[0]
        return None

    except Exception as e:
        print(f"Error getting note: {e}")
        cursor.close()
        conn.close()
        return None
