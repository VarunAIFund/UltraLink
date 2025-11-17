"""
New search module - Uses structured extraction to extract skills, then builds SQL query
"""
import os
import re
from typing import List, Optional, Literal
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from search import get_db_connection, is_safe_query

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

client = OpenAI()


class SearchCriteria(BaseModel):
    """Structured search criteria extracted from natural language query"""
    skills: List[str] = []  # e.g., ["Python", "AI", "Machine Learning"]
    seniority: Optional[Literal["Intern", "Entry", "Junior", "Mid", "Senior", "Lead", "Manager", "Director", "VP", "C-Level"]] = None


def extract_search_criteria(query: str) -> SearchCriteria:
    """Use GPT to extract structured criteria from natural language"""

    system_prompt = """Extract skills, technologies, domains, and seniority level from candidate search queries.

SENIORITY LEVELS (exact values):
Intern, Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level

SENIORITY MAPPING:
- "Senior" → "Senior"
- "Junior" → "Junior"
- "Manager" → "Manager"
- "Director" → "Director"
- "VP", "Vice President" → "VP"
- "CEO", "CTO", "CFO", "Founder", "Executive", "C-suite" → "C-Level"
- "Lead", "Tech Lead", "Team Lead" → "Lead"

RULES:
- Remove filler words: "experience", "background", "knowledge"
- Extract core terms only
- Expand abbreviations: AI → ["AI", "Artificial Intelligence"]

EXAMPLES:
"Python developers" → {"skills": ["Python"], "seniority": null}
"Senior AI engineers" → {"skills": ["AI", "Artificial Intelligence"], "seniority": "Senior"}
"Directors with retail experience" → {"skills": ["Retail"], "seniority": "Director"}
"CTOs at startups" → {"skills": [], "seniority": "C-Level"}
"""

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        response_format=SearchCriteria,
        temperature=0.1
    )

    criteria = response.choices[0].message.parsed
    print(f"[DEBUG] Extracted criteria: {criteria.model_dump_json(indent=2)}")
    return criteria


def build_sql_from_criteria(criteria: SearchCriteria) -> str:
    """Build SQL query from extracted criteria - candidates must match ALL criteria (AND logic)"""

    # Core SELECT fields
    select_fields = [
        "linkedin_url", "name", "location", "seniority", "skills",
        "headline", "connected_to", "years_experience", "worked_at_startup",
        "profile_pic", "experiences", "education"
    ]

    sql = f"SELECT {', '.join(select_fields)}\nFROM candidates\n"

    where_clauses = []

    # Add skill conditions - ALL skills must match (AND logic)
    if criteria.skills:
        for skill in criteria.skills:
            escaped_skill = re.escape(skill)
            # Search in multiple fields with OR logic:
            # - skills array: top-level skills field
            # - industry_tags: specifically within "industry_tags" array in experiences JSONB
            # Pattern matches: "industry_tags": [...<skill>...]
            industry_tags_pattern = f'"industry_tags"\\s*:\\s*\\[[^\\]]*{escaped_skill}[^\\]]*\\]'
            skill_condition = f"(array_to_string(skills, ',') ~* '{escaped_skill}' OR experiences::text ~* '{industry_tags_pattern}')"
            where_clauses.append(skill_condition)

    # Add seniority condition
    if criteria.seniority:
        where_clauses.append(f"seniority = '{criteria.seniority}'")

    # Build WHERE clause
    if where_clauses:
        sql += "WHERE " + "\n  AND ".join(where_clauses) + "\n"

    # Add limit
    sql += "LIMIT 1000;"

    return sql


def execute_search_new(query: str):
    """Main search function using structured extraction"""

    # Step 1: Extract criteria from query
    print(f"[DEBUG] Query: {query}")
    criteria = extract_search_criteria(query)

    # Step 2: Build SQL from criteria
    sql = build_sql_from_criteria(criteria)
    print(f"[DEBUG] Generated SQL:\n{sql}\n")

    # Step 3: Validate SQL
    if not is_safe_query(sql):
        raise ValueError(f"Unsafe SQL query generated:\n{sql}")

    # Step 4: Get actual total count (without LIMIT)
    count_sql = sql.replace('LIMIT 1000;', '').strip()
    count_sql = count_sql.replace('SELECT ' + ', '.join([
        "linkedin_url", "name", "location", "seniority", "skills",
        "headline", "connected_to", "years_experience", "worked_at_startup",
        "profile_pic", "experiences", "education"
    ]), 'SELECT COUNT(*)')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get total count
    cursor.execute(count_sql)
    actual_total = cursor.fetchone()[0]
    print(f"[DEBUG] Actual total matching candidates: {actual_total}")

    # Step 5: Execute main query with limit
    cursor.execute(sql)

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

    return {
        'query': query,
        'extracted_skills': criteria.skills,
        'extracted_seniority': criteria.seniority,
        'sql': sql,
        'results': results,
        'total': actual_total,  # Actual count, not limited
        'returned': len(results)  # Number of results returned (up to 1000)
    }


# Command line testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "Find Python developers"

    print(f"\n{'='*80}")
    print(f"Testing Search with Query: {query}")
    print('='*80)

    result = execute_search_new(query)

    print(f"\nExtracted Skills: {result['extracted_skills']}")
    print(f"Extracted Seniority: {result['extracted_seniority']}")
    print(f"\nGenerated SQL:\n{result['sql']}")
    print(f"\nTotal matching candidates: {result['total']}")
    print(f"Returned in results: {result['returned']} (limited to 1000)")

    if result['returned'] > 0:
        print(f"\nFirst 3 candidates:")
        for i, candidate in enumerate(result['results'][:3]):
            print(f"\n{i+1}. {candidate['name']}")
            print(f"   Location: {candidate['location']}")
            print(f"   Seniority: {candidate['seniority']}")
            print(f"   Skills: {', '.join(candidate['skills'][:5]) if candidate['skills'] else 'N/A'}")
