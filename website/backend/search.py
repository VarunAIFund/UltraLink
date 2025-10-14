"""
Search module - Handles query generation and database search
"""
import os
import re
import psycopg2
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values
from openai import OpenAI
from db_schema import get_schema_prompt

# Load environment - .env is at project root (UltraLink/)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

client = OpenAI()

def get_db_connection():
    """Get Supabase database connection via connection pooler"""
    env_vars = dotenv_values(env_path)
    supabase_url = env_vars.get('SUPABASE_URL', '')
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    db_password = env_vars.get('SUPABASE_DB_PASSWORD')
    encoded_password = quote_plus(db_password)

    # Use connection pooler for better reliability and to avoid IP restrictions
    conn_string = f"postgresql://postgres.{project_id}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
    return psycopg2.connect(conn_string)

def generate_sql(query: str) -> str:
    """Use GPT to convert natural language to SQL"""

    system_prompt = f"""You are a SQL generator for Supabase PostgreSQL. Output ONLY valid PostgreSQL SQL queries.
    {get_schema_prompt()}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{query}\n\nSQL:"}
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

    return sql

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

def execute_search(query: str):
    """Main search function"""
    # Generate SQL
    sql = generate_sql(query)

    # Validate
    if not is_safe_query(sql):
        raise ValueError(f"Unsafe SQL query generated:\n{sql}")

    # Debug: print SQL
    print(f"Generated SQL:\n{sql}\n")

    # Execute
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)

    columns = [desc[0] for desc in cursor.description]
    print(columns)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        result = {}
        for i, value in enumerate(row):
            result[columns[i]] = value
        results.append(result)

    cursor.close()
    conn.close()

    return {
        'sql': sql,
        'results': results,
        'total': len(results)
    }
