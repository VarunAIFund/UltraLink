"""
Save and retrieve search sessions from database
"""
import psycopg2
import os
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

def get_db_connection():
    """Get Supabase database connection - uses different URLs for local vs Railway"""
    # Detect if running on Railway (Railway sets RAILWAY_ENVIRONMENT_NAME)
    is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None

    if is_railway:
        # Railway: Use os.getenv() which reads from Railway environment variables
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        supabase_url = os.getenv('SUPABASE_URL', '')
    else:
        # Local: Use dotenv_values() to read directly from .env file
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

    if is_railway:
        # Railway: Use connection pooler (port 6543)
        conn_string = f"postgresql://postgres.{project_id}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
        print(f"[DEBUG] Railway detected - Using pooler: postgresql://postgres.{project_id}:****@aws-1-us-east-2.pooler.supabase.com:6543/postgres")
    else:
        # Local: Use direct connection (port 5432)
        conn_string = f"postgresql://postgres:{encoded_password}@db.{project_id}.supabase.co:5432/postgres"
        print(f"[DEBUG] Local detected - Using direct: postgresql://postgres:****@db.{project_id}.supabase.co:5432/postgres")

    return psycopg2.connect(conn_string)

def save_search_session(query, connected_to, sql_query, results, total_cost=0.0, logs='', total_time=0.0, ranking=True):
    """
    Save search session to database

    Args:
        query: Search query text
        connected_to: Filter value ('all' or connection name)
        sql_query: The SQL query that was executed
        results: List of ranked candidates
        total_cost: Total cost of the search (default: 0.0)
        logs: Console logs from search execution (default: '')
        total_time: Total execution time in seconds (default: 0.0)
        ranking: Whether Stage 2 ranking was enabled (default: True)

    Returns:
        UUID of saved search session
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prepare connected_to as array
    connected_to_array = [connected_to] if connected_to != 'all' else []

    cursor.execute("""
        INSERT INTO search_sessions (query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        query,
        connected_to_array,
        sql_query,
        json.dumps(results),
        len(results),
        total_cost,
        logs,
        total_time,
        ranking
    ))

    search_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return str(search_id)

def get_search_session(search_id):
    """
    Retrieve saved search session by UUID

    Args:
        search_id: UUID of search session

    Returns:
        Dict with search data or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled, created_at
        FROM search_sessions
        WHERE id = %s
    """, (search_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        return None

    query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled, created_at = result

    return {
        'id': search_id,
        'query': query,
        'connected_to': connected_to[0] if connected_to else 'all',
        'sql': sql_query,
        'results': results,
        'total': total_results,
        'total_cost': float(total_cost) if total_cost else 0.0,
        'logs': logs if logs else '',
        'total_time': float(total_time) if total_time else 0.0,
        'ranking_enabled': ranking_enabled if ranking_enabled is not None else True,
        'created_at': created_at.isoformat()
    }
