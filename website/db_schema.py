"""
Database schema information for GPT context when generating SQL queries.
This helps GPT understand the database structure and generate accurate queries.
"""

DATABASE_SCHEMA = """
DATABASE SCHEMA INFORMATION:

TABLE: candidates (987 records)
- linkedin_url (TEXT, PRIMARY KEY): LinkedIn profile URL
- name (TEXT, REQUIRED): Full name
- headline (TEXT): Professional headline/summary
- location (TEXT): Location in "City, State, Country" format
- phone (TEXT): Phone number
- email (TEXT): Email address
- profile_pic (TEXT): Profile picture URL
- profile_pic_high_quality (TEXT): High quality profile picture URL
- connected_to (TEXT[]): Array of mutual connections/people they're connected to
- seniority (TEXT): Seniority level - VALUES: Intern, Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level
- skills (TEXT[]): Array of skills including programming languages, technologies, and expertise areas
- years_experience (INTEGER): Total years of professional experience
- average_tenure (NUMERIC): Average tenure at companies in years
- worked_at_startup (BOOLEAN): Whether they have startup experience
- experiences (JSONB): Array of work experience objects with company, title, dates, description
- education (JSONB): Array of education objects with school, degree, field, dates
- created_at (TIMESTAMP): Record creation timestamp
- updated_at (TIMESTAMP): Last update timestamp

IMPORTANT QUERY RULES:
1. ALWAYS include these core fields in SELECT: linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
2. For skills array searches: 'Python' = ANY(skills) OR skills @> ARRAY['Python']
3. For searching in experiences JSONB: experiences::text ~* '\\mTERM\\M' (word boundary regex)
4. For searching in education JSONB: education::text ~* '\\mTERM\\M'
5. For CEOs/Executives/Founders: use seniority = 'C-Level' (NOT 'CEO' or 'Executive')
6. Location searches: use ILIKE for flexible matching (e.g., location ILIKE '%San Francisco%')
7. Connected to searches: 'Person Name' = ANY(connected_to)
8. Abbreviation expansion: When you see abbreviations (AI, ML, NLP, RAG, LLM, VC), search for BOTH the abbreviated and expanded forms (e.g., AI searches for 'AI' OR 'Artificial Intelligence')
9. ALWAYS use LIMIT 100 to cap results
10. Output ONLY the SQL query without markdown code blocks
"""

EXAMPLE_QUERIES = """
EXAMPLE QUERIES:

Natural: "Find Python developers in San Francisco"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE 'Python' = ANY(skills) AND location ILIKE '%San Francisco%'
     LIMIT 100;

Natural: "AI engineers with 5+ years experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE years_experience >= 5
     AND (skills @> ARRAY['AI'] OR skills @> ARRAY['Artificial Intelligence'] OR experiences::text ~* '\\mAI\\M')
     LIMIT 100;

Natural: "Senior engineers who worked at Google"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE seniority = 'Senior' AND experiences::text ~* '\\mGoogle\\M'
     LIMIT 100;

Natural: "Startup founders with ML experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE (seniority = 'C-Level' OR experiences::text ~* '\\mfounder\\M')
     AND (skills @> ARRAY['Machine Learning'] OR skills @> ARRAY['ML'])
     LIMIT 100;

Natural: "People connected to John Smith"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE 'John Smith' = ANY(connected_to)
     LIMIT 100;

Natural: "Stanford CS graduates"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE education::text ~* '\\mStanford\\M' AND education::text ~* '\\mComputer Science\\M'
     LIMIT 100;
"""

def get_schema_context():
    """Return complete schema context for GPT"""
    return DATABASE_SCHEMA + "\n" + EXAMPLE_QUERIES

def get_schema_prompt():
    """Return schema prompt for GPT (alias for backward compatibility)"""
    return get_schema_context()
