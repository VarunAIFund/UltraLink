"""
Database schema information for GPT context when generating SQL queries.
This helps GPT understand the database structure and generate accurate queries.
"""

# Query result limit - change this to adjust all queries at once
LIMIT_NUMBER = 500

DATABASE_SCHEMA = f"""
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
- experiences (JSONB): Array of work experience objects. Each object contains:
  * title (TEXT): Job title (e.g., "CEO", "CTO", "VP Engineering")
  * org (TEXT): Company name
  * summary (TEXT): Detailed job description
  * short_summary (TEXT): Brief summary
  * location (TEXT): Job location
  * industry_tags (TEXT[]): Array of industry tags (e.g., ["Healthcare", "AI/ML", "Fintech"])
  * company_skills (TEXT[]): Skills used at this company
  * business_model (TEXT): e.g., "B2B", "B2C"
  * product_type (TEXT): e.g., "SaaS", "Hardware", "Platform"
- education (JSONB): Array of education objects with school, degree, field, dates
- created_at (TIMESTAMP): Record creation timestamp
- updated_at (TIMESTAMP): Last update timestamp

IMPORTANT QUERY RULES:
1. ALWAYS include these core fields in SELECT: linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup, profile_pic, experiences, education
2. For skills array searches: Use case-insensitive text search: array_to_string(skills, ',') ~* '\\mpython\\M'
3. For COMPANY searches ("worked at X", "engineers at X", "people from X"): ONLY search the org field using JSONB array traversal:
   SELECT DISTINCT c.linkedin_url, c.name, ... FROM candidates c, jsonb_array_elements(c.experiences) AS exp
   WHERE exp->>'org' ~* '\\mCOMPANY\\M'
4. For job description/responsibility searches (NOT company employment): Use full text search: experiences::text ~* '\\mTERM\\M'
5. For searching in education JSONB: education::text ~* '\\mTERM\\M'
6. For CEOs/Executives/Founders: use seniority = 'C-Level' (NOT 'CEO' or 'Executive')
7. Location searches: use ILIKE for flexible matching (e.g., location ILIKE '%San Francisco%')
8. Connected to searches: 'Person Name' = ANY(connected_to)
9. Abbreviation expansion: When you see abbreviations (AI, ML, NLP, RAG, LLM, VC), search for BOTH the abbreviated and expanded forms
10. For industry_tags searches: Use case-insensitive regex: exp->>'industry_tags' ~* '\\mhealthcare\\M' (NOT @> operator)
11. For company_skills searches: Use case-insensitive regex: exp->>'company_skills' ~* '\\mpython\\M'
12. ALWAYS use LIMIT {LIMIT_NUMBER} to cap results
13. Output ONLY the SQL query without markdown code blocks
"""

EXAMPLE_QUERIES = f"""
EXAMPLE QUERIES:

Natural: "Find Python developers in San Francisco"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup, profile_pic, experiences, education
     FROM candidates
     WHERE array_to_string(skills, ',') ~* '\\mpython\\M' AND location ILIKE '%San Francisco%'
     LIMIT {LIMIT_NUMBER};

Natural: "AI engineers with 5+ years experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup, profile_pic, experiences, education
     FROM candidates
     WHERE years_experience >= 5
     AND (array_to_string(skills, ',') ~* '\\m(ai|artificial intelligence)\\M' OR experiences::text ~* '\\mAI\\M')
     LIMIT {LIMIT_NUMBER};

Natural: "Senior engineers who worked at Google"
SQL: SELECT DISTINCT c.linkedin_url, c.name, c.location, c.seniority, c.skills, c.headline, c.connected_to, c.years_experience, c.worked_at_startup, c.profile_pic, c.experiences, c.education
     FROM candidates c, jsonb_array_elements(c.experiences) AS exp
     WHERE c.seniority = 'Senior' AND exp->>'org' ~* '\\mGoogle\\M'
     LIMIT {LIMIT_NUMBER};

Natural: "Startup founders with ML experience"
SQL: SELECT DISTINCT c.linkedin_url, c.name, c.location, c.seniority, c.skills, c.headline, c.connected_to, c.years_experience, c.worked_at_startup, c.profile_pic, c.experiences, c.education
     FROM candidates c, jsonb_array_elements(c.experiences) AS exp
     WHERE (c.seniority = 'C-Level' OR exp->>'title' ~* '\\mfounder\\M')
     AND array_to_string(c.skills, ',') ~* '\\m(ml|machine learning)\\M'
     LIMIT {LIMIT_NUMBER};

Natural: "People who worked at Stripe"
SQL: SELECT DISTINCT c.linkedin_url, c.name, c.location, c.seniority, c.skills, c.headline, c.connected_to, c.years_experience, c.worked_at_startup, c.profile_pic, c.experiences, c.education
     FROM candidates c, jsonb_array_elements(c.experiences) AS exp
     WHERE exp->>'org' ~* '\\mStripe\\M'
     LIMIT {LIMIT_NUMBER};

Natural: "People connected to John Smith"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup, profile_pic, experiences, education
     FROM candidates
     WHERE 'John Smith' = ANY(connected_to)
     LIMIT {LIMIT_NUMBER};

Natural: "Stanford CS graduates"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup, profile_pic, experiences, education
     FROM candidates
     WHERE education::text ~* '\\mStanford\\M' AND education::text ~* '\\mComputer Science\\M'
     LIMIT {LIMIT_NUMBER};

Natural: "CEO at healthcare company"
SQL: SELECT DISTINCT c.linkedin_url, c.name, c.location, c.seniority, c.skills, c.headline, c.connected_to, c.years_experience, c.worked_at_startup, c.profile_pic, c.experiences, c.education
     FROM candidates c, jsonb_array_elements(c.experiences) AS exp
     WHERE c.seniority = 'C-Level'
     AND exp->>'title' ~* '\\m(CEO|Chief Executive|Founder|Co-Founder)\\M'
     AND exp->>'industry_tags' ~* '\\mhealthcare\\M'
     LIMIT {LIMIT_NUMBER};

Natural: "CTO who worked at AI startups"
SQL: SELECT DISTINCT c.linkedin_url, c.name, c.location, c.seniority, c.skills, c.headline, c.connected_to, c.years_experience, c.worked_at_startup, c.profile_pic, c.experiences, c.education
     FROM candidates c, jsonb_array_elements(c.experiences) AS exp
     WHERE exp->>'title' ~* '\\m(CTO|Chief Technology Officer)\\M'
     AND exp->>'industry_tags' ~* '\\mai/ml\\M'
     LIMIT {LIMIT_NUMBER};
"""

def get_schema_context():
    """Return complete schema context for GPT"""
    return DATABASE_SCHEMA + "\n" + EXAMPLE_QUERIES

def get_schema_prompt():
    """Return schema prompt for GPT (alias for backward compatibility)"""
    return get_schema_context()
