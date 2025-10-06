#!/usr/bin/env python3
"""
Natural Language Candidate Search using ChatGPT + Supabase

This script accepts natural language queries and returns candidate records
by using ChatGPT to generate appropriate SQL queries for Supabase.

Usage:
    python candidate_search.py "Find Python developers in San Francisco"
    python candidate_search.py "Senior engineers who worked at startups"
    python candidate_search.py "Show me candidates with React and Node.js"
    python candidate_search.py "Directors with AI/ML industry experience"
    python candidate_search.py "People who worked at B2B companies"
"""

import sys
import json
import re
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Add transform_data directory to Python path to find our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'transform_data'))

from supabase_config import get_supabase_client
from db_schema_info import get_schema_context

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize OpenAI client
client = OpenAI()

def is_safe_query(sql: str) -> bool:
    """
    Check if the SQL query is safe (read-only, no dangerous operations)
    """
    sql_upper = sql.upper().strip()
    
    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False
    
    # Dangerous keywords not allowed
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
        'TRUNCATE', 'REPLACE', 'MERGE', 'CALL', 'EXEC'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True

def extract_sql_from_response(response: str) -> Optional[str]:
    """
    Extract SQL query from ChatGPT response, handling various formats
    """
    # Try to find SQL in code blocks
    code_block_pattern = r'```(?:sql)?\s*(.*?)\s*```'
    match = re.search(code_block_pattern, response, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    # Try to find SQL that starts with SELECT
    select_pattern = r'(SELECT.*?;?)\s*$'
    match = re.search(select_pattern, response, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    
    # If no clear SQL found, return the whole response (user can debug)
    return response.strip()

def expand_abbreviations(query: str) -> str:
    """
    Expand common abbreviations in queries
    """
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

    import re
    expanded_query = query
    for abbr, expansion in abbreviations.items():
        if re.search(abbr, query, re.IGNORECASE):
            expanded_query = re.sub(abbr, expansion, expanded_query, flags=re.IGNORECASE)

    return expanded_query

def generate_sql_query(natural_query: str) -> str:
    """
    Use ChatGPT to convert natural language query to SQL for Supabase
    """
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

def execute_candidate_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute the SQL query using Supabase and return candidate records
    """
    if not is_safe_query(sql_query):
        raise ValueError("Query contains unsafe operations. Only SELECT queries are allowed.")

    try:
        # Use Supabase MCP tool to execute raw SQL
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

        # Get project ID from environment
        from dotenv import dotenv_values
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        env_vars = dotenv_values(env_path)
        supabase_url = env_vars.get('SUPABASE_URL', '')
        project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')

        # Execute SQL via MCP
        from anthropic import Anthropic
        anthropic_client = Anthropic()

        # For now, use direct SQL execution via psycopg2
        # This is simpler than using MCP from within the script
        import psycopg2
        from urllib.parse import quote_plus
        db_password = env_vars.get('SUPABASE_DB_PASSWORD')

        # URL-encode the password to handle special characters
        encoded_password = quote_plus(db_password)

        # Construct postgres connection string for direct connection
        conn_string = f"postgresql://postgres:{encoded_password}@db.{project_id}.supabase.co:5432/postgres"

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Fetch all results
        rows = cursor.fetchall()

        # Convert to list of dictionaries
        candidates = []
        for row in rows:
            candidate = {}
            for i, value in enumerate(row):
                # Handle array and JSON fields
                if isinstance(value, list):
                    candidate[columns[i]] = value
                elif value is not None:
                    candidate[columns[i]] = value
                else:
                    candidate[columns[i]] = None
            candidates.append(candidate)

        cursor.close()
        conn.close()

        return candidates

    except Exception as e:
        raise Exception(f"Database query error: {e}")

def format_results(candidates: List[Dict[str, Any]], format_type: str = "json") -> str:
    """
    Format candidate results for display
    """
    if not candidates:
        return "No candidates found matching your query."
    
    if format_type == "json":
        return json.dumps(candidates, indent=2, default=str)
    
    elif format_type == "table":
        # Simple table format
        if not candidates:
            return "No results found."
        
        # Get common fields to display
        common_fields = ['name', 'location', 'seniority', 'years_experience']
        available_fields = [field for field in common_fields if field in candidates[0]]
        
        # Create header
        header = " | ".join(field.replace('_', ' ').title() for field in available_fields)
        separator = "-" * len(header)
        
        # Create rows
        rows = []
        for candidate in candidates:
            row_values = []
            for field in available_fields:
                value = candidate.get(field, "N/A")
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:3])  # Show first 3 items
                row_values.append(str(value)[:20])  # Truncate long values
            
            rows.append(" | ".join(row_values))
        
        return f"{header}\n{separator}\n" + "\n".join(rows)
    
    return str(candidates)

def search_candidates(natural_query: str, output_format: str = "json") -> str:
    """
    Main function to search candidates using natural language
    """
    try:
        print(f"🔍 Processing query: {natural_query}")

        # Generate SQL from natural language
        sql_query = generate_sql_query(natural_query)
        print(f"\n🔧 Generated SQL:")
        print(f"{sql_query}\n")

        # Execute query
        candidates = execute_candidate_query(sql_query)
        print(f"✅ Found {len(candidates)} candidates")

        # Format and return results
        return format_results(candidates, output_format)

    except Exception as e:
        return f"❌ Error: {e}"

def interactive_mode():
    """
    Interactive mode for continuous querying
    """
    print("🚀 UltraLink Candidate Search (Supabase)")
    print("Enter natural language queries to find candidates.")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'help' for example queries.\n")

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if query.lower() == 'help':
                print("\nExample queries:")
                print("- Find Python developers in San Francisco")
                print("- Senior engineers who worked at Google")
                print("- Show me candidates with AI and machine learning skills")
                print("- Directors with startup experience")
                print("- People who worked in fintech B2B companies")
                print("- Candidates with AI/ML industry experience")
                print("- C-Level executives with 10+ years experience")
                print()
                continue

            if not query:
                continue

            print()  # Empty line for readability
            result = search_candidates(query, "table")
            print(result)
            print()  # Empty line after results

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """
    Main entry point
    """
    if len(sys.argv) < 2:
        # No arguments - start interactive mode
        interactive_mode()
        return
    
    # Command line mode
    natural_query = " ".join(sys.argv[1:])
    
    # Check for output format flag
    output_format = "json"
    if "--table" in sys.argv:
        output_format = "table"
        natural_query = natural_query.replace("--table", "").strip()
    
    result = search_candidates(natural_query, output_format)
    print(result)

if __name__ == "__main__":
    main()