"""
Save and retrieve search sessions from database
"""
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import os
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values
from contextlib import contextmanager

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Global connection pool
connection_pool = None

def init_connection_pool():
    """Initialize connection pool with 3-5 persistent connections"""
    global connection_pool

    if connection_pool is not None:
        return  # Already initialized

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

    # Create THREADED pool with 3-5 connections (thread-safe for Flask + background threads)
    connection_pool = ThreadedConnectionPool(3, 5, conn_string)
    print("[POOL] Thread-safe connection pool initialized (3-5 connections)")

@contextmanager
def get_pooled_connection():
    """Get a connection from the pool, automatically return it when done"""
    if connection_pool is None:
        init_connection_pool()

    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def save_search_session(query, connected_to, sql_query='', results=None, total_cost=0.0, logs='', total_time=0.0, ranking=True, status='searching'):
    """
    Save search session to database

    Args:
        query: Search query text
        connected_to: Filter value ('all' or connection name)
        sql_query: The SQL query that was executed (default: '')
        results: List of ranked candidates (default: None = empty list)
        total_cost: Total cost of the search (default: 0.0)
        logs: Console logs from search execution (default: '')
        total_time: Total execution time in seconds (default: 0.0)
        ranking: Whether Stage 2 ranking was enabled (default: True)
        status: Current status of search (default: 'searching')

    Returns:
        UUID of saved search session
    """
    # Default results to empty list if None
    if results is None:
        results = []

    with get_pooled_connection() as conn:
        cursor = conn.cursor()

        # Prepare connected_to as array
        connected_to_array = [connected_to] if connected_to != 'all' else []

        cursor.execute("""
            INSERT INTO search_sessions (query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            ranking,
            status
        ))

        search_id = cursor.fetchone()[0]
        conn.commit()

        return str(search_id)

def update_search_session(search_id, sql_query=None, results=None, total_cost=None, logs=None, total_time=None, status=None):
    """
    Update an existing search session with results and/or status

    Args:
        search_id: UUID of search session to update
        sql_query: The SQL query that was executed (optional, won't update if None)
        results: List of ranked candidates (optional, won't update if None)
        total_cost: Total cost of the search (optional, won't update if None)
        logs: Console logs from search execution (optional, won't update if None)
        total_time: Total execution time in seconds (optional, won't update if None)
        status: Current status of search (optional, won't update if None)

    Returns:
        UUID of updated search session
    """
    # Build dynamic UPDATE query based on what's provided
    updates = []
    params = []

    if sql_query is not None:
        updates.append("sql_query = %s")
        params.append(sql_query)

    if results is not None:
        updates.extend(["results = %s", "total_results = %s"])
        params.extend([json.dumps(results), len(results)])

    if total_cost is not None:
        updates.append("total_cost = %s")
        params.append(total_cost)

    if logs is not None:
        updates.append("logs = %s")
        params.append(logs)

    if total_time is not None:
        updates.append("total_time = %s")
        params.append(total_time)

    if status is not None:
        updates.append("status = %s")
        params.append(status)

    # If nothing to update, return early
    if not updates:
        return str(search_id)

    # Add search_id to params
    params.append(search_id)

    with get_pooled_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            UPDATE search_sessions
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id
        """, params)

        updated_id = cursor.fetchone()
        conn.commit()

        return str(updated_id[0]) if updated_id else None

def get_search_session(search_id):
    """
    Retrieve saved search session by UUID

    Args:
        search_id: UUID of search session

    Returns:
        Dict with search data or None if not found
    """
    with get_pooled_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled, status, created_at
            FROM search_sessions
            WHERE id = %s
        """, (search_id,))

        result = cursor.fetchone()

        if not result:
            return None

        query, connected_to, sql_query, results, total_results, total_cost, logs, total_time, ranking_enabled, status, created_at = result

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
            'status': status if status else 'searching',
            'created_at': created_at.isoformat()
        }
