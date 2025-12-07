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


def validate_user(username):
    """
    Check if user exists

    Args:
        username: Username to validate

    Returns:
        dict: User info if valid, None if invalid
        {
            'username': 'linda',
            'display_name': 'Linda Smith',
            'email': 'linda@company.com'
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM users
            WHERE username = %s
        """, (username,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        return dict(user) if user else None
    except Exception as e:
        print(f"Error validating user: {e}")
        return None


def get_all_users():
    """
    Get all users

    Returns:
        list: Array of user objects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM users
            ORDER BY display_name
        """)

        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(user) for user in users]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
