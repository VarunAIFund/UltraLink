#!/usr/bin/env python3
"""
Flask web application for UltraLink Candidate Search with AI-powered natural language queries

Usage:
    python app.py
    Then open http://localhost:5001 in your browser
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
import re

# Add transform_data directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'transform_data'))

from dotenv import load_dotenv, dotenv_values
import psycopg2
from urllib.parse import quote_plus
from openai import OpenAI
from db_schema_info import get_schema_context

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI()

def get_db_connection():
    """Get Supabase database connection"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_vars = dotenv_values(env_path)
    supabase_url = env_vars.get('SUPABASE_URL', '')
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    db_password = env_vars.get('SUPABASE_DB_PASSWORD')
    encoded_password = quote_plus(db_password)

    conn_string = f"postgresql://postgres:{encoded_password}@db.{project_id}.supabase.co:5432/postgres"
    return psycopg2.connect(conn_string)

def expand_abbreviations(query: str) -> str:
    """Expand common abbreviations in queries"""
    abbreviations = {
        r'\bVC\b': 'venture capital OR VC',
        r'\bAI\b': 'artificial intelligence OR AI',
        r'\bML\b': 'machine learning OR ML',
        r'\bNLP\b': 'natural language processing OR NLP',
        r'\bSaaS\b': 'Software as a Service OR SaaS',
        r'\bAPI\b': 'application programming interface OR API',
        r'\bCEO\b': 'Chief Executive Officer OR CEO',
        r'\bCTO\b': 'Chief Technology Officer OR CTO',
        r'\bVP\b': 'Vice President OR VP',
        r'\bPM\b': 'product management OR product manager OR PM',
        r'\bUI/UX\b': 'user interface OR user experience OR UI/UX',
        r'\bDevOps\b': 'development operations OR DevOps',
        r'\bMLOps\b': 'machine learning operations OR MLOps',
        r'\bRAG\b': 'retrieval augmented generation OR RAG OR retrieval-augmented',
        r'\bLLM\b': 'large language model OR LLM',
    }

    expanded_query = query
    for abbr, expansion in abbreviations.items():
        if re.search(abbr, query, re.IGNORECASE):
            expanded_query = re.sub(abbr, expansion, expanded_query, flags=re.IGNORECASE)

    return expanded_query

def generate_sql_query(natural_query: str) -> str:
    """Use ChatGPT to convert natural language query to SQL for Supabase"""
    # Expand abbreviations before sending to AI
    expanded_query = expand_abbreviations(natural_query)

    system_prompt = f"""
You are a SQL generator for Supabase PostgreSQL. Output ONLY valid PostgreSQL SQL queries. No explanations, no code blocks, no formatting.

{get_schema_context()}

RULES:
- Always SELECT from candidates table (single table with JSONB fields)
- For skills search: Use 'skill' = ANY(skills) or skills && ARRAY['skill1', 'skill2']
- For industry_tags/business_model: Use experiences::text ILIKE pattern or JSONB operators
- When query contains "OR" for synonyms, use ILIKE with multiple conditions: (experiences::text ILIKE '%term1%' OR experiences::text ILIKE '%term2%')
- Include WHERE clauses for filtering
- Always include linkedin_url in SELECT
- End with LIMIT 100
- Output only the SQL query
    """

    user_prompt = f"{expanded_query}\n\nSQL:"

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        sql_query = completion.choices[0].message.content.strip()

        # Remove any potential SQL prefix if present
        if sql_query.startswith('SQL:'):
            sql_query = sql_query[4:].strip()

        return sql_query

    except Exception as e:
        raise Exception(f"Error generating SQL query: {e}")

def is_safe_query(sql: str) -> bool:
    """Check if the SQL query is safe (read-only, no dangerous operations)"""
    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False

    # Dangerous keywords not allowed (use word boundaries to avoid false positives)
    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bREPLACE\b',
        r'\bMERGE\b', r'\bCALL\b', r'\bEXEC\b', r'\bEXECUTE\b'
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            return False

    return True

def execute_search_query(sql_query):
    """Execute SQL query and return results"""
    if not is_safe_query(sql_query):
        raise ValueError("Query contains unsafe operations. Only SELECT queries are allowed.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = {}
            for i, value in enumerate(row):
                result[columns[i]] = value
            results.append(result)

        cursor.close()
        conn.close()

        return results
    except Exception as e:
        print(f"Database error: {e}")
        raise

@app.route('/')
def index():
    """Main search page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for AI-powered natural language search"""
    data = request.json
    query = data.get('query', '').strip()

    if not query:
        return jsonify({
            'success': False,
            'error': 'Please enter a search query'
        })

    try:
        # Generate SQL from natural language using AI
        sql_query = generate_sql_query(query)

        # Execute the query
        results = execute_search_query(sql_query)

        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'sql': sql_query,
            'expanded_query': expand_abbreviations(query)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'sql': sql_query if 'sql_query' in locals() else None
        })

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total candidates
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total = cursor.fetchone()[0]

        # By seniority
        cursor.execute("""
            SELECT seniority, COUNT(*)
            FROM candidates
            WHERE seniority IS NOT NULL
            GROUP BY seniority
            ORDER BY COUNT(*) DESC
        """)
        seniority_stats = dict(cursor.fetchall())

        # Top skills
        cursor.execute("""
            SELECT unnest(skills) as skill, COUNT(*) as count
            FROM candidates
            WHERE skills IS NOT NULL
            GROUP BY skill
            ORDER BY count DESC
            LIMIT 20
        """)
        top_skills = [{'skill': row[0], 'count': row[1]} for row in cursor.fetchall()]

        # Startup experience
        cursor.execute("""
            SELECT worked_at_startup, COUNT(*)
            FROM candidates
            WHERE worked_at_startup IS NOT NULL
            GROUP BY worked_at_startup
        """)
        startup_stats = dict(cursor.fetchall())

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'total': total,
            'seniority': seniority_stats,
            'top_skills': top_skills,
            'startup_experience': startup_stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
