"""
Receiver management - Get info about connection owners (people whose networks were uploaded)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import quote_plus


def get_db_connection():
    """Get database connection (Railway vs local)"""
    password = os.getenv('SUPABASE_DB_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')

    if not password:
        raise ValueError("SUPABASE_DB_PASSWORD environment variable is not set")
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")

    # Extract project ID from Supabase URL
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    encoded_password = quote_plus(password)

    # Always use connection pooler (port 6543) for better performance and stability
    conn_string = f"postgresql://postgres.{project_id}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

    return psycopg2.connect(conn_string)


def get_receiver(username):
    """
    Get receiver information by username

    Args:
        username: Username to lookup (e.g., 'dan', 'rishabh')

    Returns:
        dict: Receiver info if found, None if not found
        {
            'username': 'rishabh',
            'display_name': 'Rishabh Sharma',
            'email': 'rishabh@aifund.ai'
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM receivers
            WHERE username = %s
        """, (username.lower(),))

        receiver = cursor.fetchone()
        cursor.close()
        conn.close()

        return dict(receiver) if receiver else None
    except Exception as e:
        print(f"Error getting receiver: {e}")
        return None


def get_all_receivers():
    """
    Get all receivers

    Returns:
        list: Array of receiver objects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM receivers
            ORDER BY display_name
        """)

        receivers = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(receiver) for receiver in receivers]
    except Exception as e:
        print(f"Error getting receivers: {e}")
        return []
