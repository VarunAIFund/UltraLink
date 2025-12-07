"""
Search module - Handles query generation and database search
"""
import os
import re
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values
from contextlib import contextmanager
from openai import OpenAI
from db_schema import get_schema_prompt
from utils import add_profile_pic_urls
from constants import SQL_GENERATION_MODEL, SQL_QUERY_LIMIT

# Load environment - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

client = OpenAI()

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

    # Test if connection is stale (closed by database server)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except psycopg2.OperationalError:
        # Connection is stale, close it and get a fresh one
        print("[POOL] Detected stale connection, getting fresh one...")
        conn.close()
        connection_pool.putconn(conn, close=True)
        conn = connection_pool.getconn()

    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def generate_sql(query: str, connected_to: str = None) -> str:
    """Use GPT to convert natural language to SQL"""

    system_prompt = f"""You are a SQL generator for Supabase PostgreSQL. Output ONLY valid PostgreSQL SQL queries.
    {get_schema_prompt()}"""

    # Add connection filter if specified
    user_query = query
    if connected_to and connected_to.lower() != 'all':
        # Handle multiple connections with OR logic
        connections = [c.strip().lower() for c in connected_to.split(',')]
        if len(connections) > 1:
            or_conditions = ' OR '.join([f"array_to_string(connected_to, ',') ~* '\\m{conn}\\M'" for conn in connections])
            user_query = f"{query}\n\nIMPORTANT: Also filter for people connected to any of these: {', '.join(connections)}. Use this WHERE clause: ({or_conditions})"
        else:
            user_query = f"{query}\n\nIMPORTANT: Also filter for people connected to '{connected_to}' using: array_to_string(connected_to, ',') ~* '\\m{connected_to}\\M'"

    response = client.chat.completions.create(
        model=SQL_GENERATION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_query}\n\nSQL:"}
        ],
        temperature=0.1
    )

    sql = response.choices[0].message.content.strip()

    # Strip markdown code blocks if present
    if sql.startswith('```'):
        sql = sql.split('```')[1]
        if sql.startswith('sql'):
            sql = sql[3:]
        sql = sql.strip()

    # Track token usage and cost
    usage = response.usage
    tokens_used = {
        'input_tokens': usage.prompt_tokens,
        'output_tokens': usage.completion_tokens,
        'total_tokens': usage.total_tokens
    }

    # GPT-4o-mini pricing: $0.150 per 1M input, $0.600 per 1M output
    cost_input = (tokens_used['input_tokens'] / 1_000_000) * 0.150
    cost_output = (tokens_used['output_tokens'] / 1_000_000) * 0.600
    total_cost = cost_input + cost_output

    print(f"\n💰 SQL Generation Cost ({SQL_GENERATION_MODEL}):")
    print(f"   • Input tokens: {tokens_used['input_tokens']:,} (${cost_input:.4f})")
    print(f"   • Output tokens: {tokens_used['output_tokens']:,} (${cost_output:.4f})")
    print(f"   • Total cost: ${total_cost:.4f}")

    cost_data = {
        'input_tokens': tokens_used['input_tokens'],
        'output_tokens': tokens_used['output_tokens'],
        'total_tokens': tokens_used['total_tokens'],
        'cost_input': cost_input,
        'cost_output': cost_output,
        'total_cost': total_cost
    }

    return sql, cost_data

def is_safe_query(sql: str) -> bool:
    """Check if SQL is safe"""
    sql_upper = sql.upper().strip()

    if not sql_upper.startswith('SELECT'):
        return False

    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bEXEC\b'
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            return False

    return True

def generate_relaxed_query(original_query: str, connected_to: str = None) -> str:
    """Generate a more relaxed/broader version of the query for progressive search"""

    relaxation_prompt = f"""The original query "{original_query}" returned too few results.

Generate a BROADER, more RELAXED version of the SQL query by following these principles:

WHAT TO KEEP STRICT:
- Seniority levels (e.g., if looking for executives, keep Director/VP/C-Level, don't downgrade to Mid/Senior)
- Years of experience requirements
- Location constraints (if specified)

WHAT TO BROADEN:
- KEYWORDS and SKILLS: Expand to synonyms and related terms
  * Think semantically: what other terms mean the same thing?
  * Example concept: "digital experience" could also be "digital transformation", "ecommerce", "online", "omnichannel", "digital strategy"
  * Example concept: "AI" could also be "artificial intelligence", "machine learning", "ML"

- FIELDS TO SEARCH: Look in multiple places
  * Search in: job titles (exp->>'title'), job descriptions (exp->>'summary'), headline, skills array, full experiences text
  * Use OR conditions to search the same concept across multiple fields

- MATCHING LOGIC: Use OR instead of AND for related concepts
  * Instead of: title must contain X AND Y
  * Try: title OR summary OR headline contains (X OR X-synonym) OR (Y OR Y-synonym)

IMPORTANT: Keep all candidates relevant to the original query intent, just broaden how you find them.

Generate a broader SQL query for: {original_query}"""

    return generate_sql(relaxation_prompt, connected_to)

def wrap_sql_with_bookmark_check(sql: str, user_name: str) -> str:
    """Wrap SQL query with LEFT JOIN to user_bookmarks to get is_bookmarked status"""
    # Remove trailing semicolon if present (causes syntax error in subquery)
    sql = sql.rstrip().rstrip(';')

    return f"""
SELECT candidate_data.*,
       CASE WHEN ub.id IS NOT NULL THEN true ELSE false END as is_bookmarked
FROM (
    {sql}
) AS candidate_data
LEFT JOIN user_bookmarks ub
    ON candidate_data.linkedin_url = ub.linkedin_url
    AND ub.user_name = '{user_name}'
"""

def execute_search(query: str, connected_to: str = None, min_results: int = 10, user_name: str = None):
    """Main search function with progressive relaxation if results are too few

    Args:
        query: Natural language search query
        connected_to: Filter by connection (e.g., 'linda', 'dan', 'all')
        min_results: Minimum results threshold for relaxed search
        user_name: Optional username to check bookmark status
    """

    # Generate SQL
    sql, sql_cost = generate_sql(query, connected_to)

    # Validate
    if not is_safe_query(sql):
        raise ValueError(f"Unsafe SQL query generated:\n{sql}")

    # Wrap SQL with bookmark check if user_name provided
    if user_name:
        sql = wrap_sql_with_bookmark_check(sql, user_name)

    # Debug: print SQL
    print(f"[SEARCH] Generated SQL:\n{sql}\n")

    # Execute with pooled connection
    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = {}
            for i, value in enumerate(row):
                result[columns[i]] = value
            results.append(result)

        print(f"[SEARCH] Initial search returned {len(results)} results")

        # If too few results, try a more relaxed search
        if len(results) < min_results:
            print(f"[SEARCH] Too few results ({len(results)} < {min_results}), trying relaxed search...")

            try:
                relaxed_sql, relaxed_cost = generate_relaxed_query(query, connected_to)

                # Validate relaxed query
                if not is_safe_query(relaxed_sql):
                    print(f"[SEARCH] Relaxed query unsafe, using original results")
                else:
                    # Wrap relaxed SQL with bookmark check if user_name provided
                    if user_name:
                        relaxed_sql = wrap_sql_with_bookmark_check(relaxed_sql, user_name)

                    print(f"[SEARCH] Relaxed SQL:\n{relaxed_sql}\n")

                    # Execute relaxed query
                    cursor.execute(relaxed_sql)
                    relaxed_rows = cursor.fetchall()

                    relaxed_results = []
                    for row in relaxed_rows:
                        result = {}
                        for i, value in enumerate(row):
                            result[columns[i]] = value
                        relaxed_results.append(result)

                    print(f"[SEARCH] Relaxed search returned {len(relaxed_results)} results")

                    # Use relaxed results if they're better
                    if len(relaxed_results) > len(results):
                        print(f"[SEARCH] Using relaxed results ({len(relaxed_results)} results)")
                        results = relaxed_results
                        sql = relaxed_sql  # Update SQL to show the one that was actually used
                        sql_cost = relaxed_cost  # Update cost to match the query that was used
                    else:
                        print(f"[SEARCH] Keeping original results ({len(results)} results)")

            except Exception as e:
                print(f"[SEARCH] Relaxed search failed: {e}, using original results")

    # Add profile pic URLs to results
    results = add_profile_pic_urls(results)

    return {
        'sql': sql,
        'results': results,
        'total': len(results),
        'cost': sql_cost
    }
