"""
Database schema information for ChatGPT context when generating SQL queries.
This helps ChatGPT understand the database structure and generate accurate queries.
"""

DATABASE_SCHEMA = """
DATABASE SCHEMA INFORMATION:

TABLE: candidates
- id (UUID): Unique candidate identifier
- name (TEXT): Full name
- location (TEXT): Location in "City, State, Country" format
- seniority (TEXT): Seniority level (Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level)
- skills (TEXT[]): Array of skills including programming languages
- years_experience (INTEGER): Total years of professional experience
- worked_at_startup (BOOLEAN): Whether they worked at startups
- headline (TEXT): Professional headline/summary
- stage (TEXT): Current recruitment stage
- confidentiality (TEXT): Confidentiality level
- emails (TEXT[]): Array of email addresses
- links (TEXT[]): Array of profile links
- tags (TEXT[]): Array of tags/labels
- created_at, updated_at (BIGINT): Timestamps

TABLE: positions  
- candidate_id (UUID): References candidates.id
- org (TEXT): Organization/company name
- title (TEXT): Job title
- summary (TEXT): Job description/summary
- short_summary (TEXT): Brief job summary
- location (TEXT): Job location
- start_date, end_date (DATE): Employment dates

TABLE: education
- candidate_id (UUID): References candidates.id  
- school (TEXT): University/institution name
- degree (TEXT): Degree type (Bachelor, Master, PhD, etc.)
- field (TEXT): Field of study

IMPORTANT QUERY RULES:
1. ALWAYS return candidate records - focus your SELECT on the candidates table
2. Use JOINs when you need to filter by positions or education data
3. Use array operators for skills: 'Python' = ANY(skills) or skills @> ARRAY['Python']
4. Location searches should use ILIKE for flexible matching
5. Always include candidate.id, name, and other relevant candidate fields
6. Limit results to maximum 100 candidates
"""

EXAMPLE_QUERIES = """
EXAMPLE QUERIES:

Natural: "Find Python developers in San Francisco"
SQL: SELECT id, name, location, seniority, skills FROM candidates 
     WHERE 'Python' = ANY(skills) AND location ILIKE '%San Francisco%' LIMIT 100;

Natural: "Senior engineers who worked at Meta"  
SQL: SELECT DISTINCT c.id, c.name, c.location, c.seniority, c.skills 
     FROM candidates c 
     JOIN positions p ON c.id = p.candidate_id 
     WHERE c.seniority = 'Senior' AND p.org ILIKE '%Meta%' LIMIT 100;

Natural: "Candidates with 5+ years experience in AI"
SQL: SELECT id, name, location, seniority, years_experience, skills 
     FROM candidates 
     WHERE years_experience >= 5 
     AND (skills @> ARRAY['AI'] OR skills @> ARRAY['Machine Learning']) LIMIT 100;

Natural: "Show me startup founders"
SQL: SELECT DISTINCT c.id, c.name, c.location, c.seniority 
     FROM candidates c 
     JOIN positions p ON c.id = p.candidate_id 
     WHERE p.title ILIKE '%founder%' OR p.title ILIKE '%co-founder%' LIMIT 100;
"""

def get_schema_context():
    """Return complete schema context for ChatGPT"""
    return DATABASE_SCHEMA + "\n" + EXAMPLE_QUERIES