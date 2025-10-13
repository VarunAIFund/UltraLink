"""
Database schema information for ChatGPT context when generating SQL queries.
This helps ChatGPT understand the Supabase database structure and generate accurate queries.
"""

DATABASE_SCHEMA = """
DATABASE SCHEMA INFORMATION (SUPABASE):

TABLE: candidates (single denormalized table with JSONB fields)
- linkedin_url (TEXT): LinkedIn profile URL - PRIMARY KEY
- name (TEXT): Full name
- headline (TEXT): Professional headline/summary
- location (TEXT): Location in "City, State, Country" format
- phone (TEXT): Phone number
- email (TEXT): Email address
- profile_pic (TEXT): Profile picture URL
- profile_pic_high_quality (TEXT): High quality profile picture URL
- connected_to (TEXT[]): Array of connection names
- seniority (TEXT): Seniority level - MUST use exact values: Intern, Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level
- skills (TEXT[]): Array of technical and domain skills
- years_experience (INTEGER): Total years of professional experience
- average_tenure (NUMERIC): Average years per position
- worked_at_startup (BOOLEAN): Whether they worked at startups
- experiences (JSONB): Array of work experiences with nested fields:
  - org (TEXT): Company name
  - company_url (TEXT): LinkedIn company URL
  - title (TEXT): Job title
  - summary (TEXT): Full job description
  - short_summary (TEXT): Brief 1-2 sentence summary
  - location (TEXT): Job location
  - company_skills (TEXT[]): Skills used in this role
  - business_model (TEXT): B2B, B2C, B2B2C, C2C, B2G
  - product_type (TEXT): SaaS, Platform, Mobile App, etc.
  - industry_tags (TEXT[]): Industry classifications (e.g., ai/ml, fintech, mobility)
- education (JSONB): Array of educational background with nested fields:
  - school (TEXT): Institution name
  - degree (TEXT): Degree level
  - field (TEXT): Field of study
- created_at, updated_at (TIMESTAMP): Timestamps

IMPORTANT QUERY RULES:
1. ALWAYS return candidate records - focus your SELECT on the candidates table
2. ALWAYS include these fields in SELECT: linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
3. For exact skill matches: 'Python' = ANY(skills) or skills @> ARRAY['Python']
4. For broad skill searches (e.g., "AI developers"), match related terms in skills OR headline:
   - Use regex on unnest(skills): EXISTS (SELECT 1 FROM unnest(skills) s WHERE s ~* '\mAI\M|LLM|NLP')
   - Or check headline: headline ~* '\mAI\M|LLM|NLP'
5. For tech experience searches (e.g., "with RAG experience"), use BOTH skills AND experiences:
   - Check skills: 'RAG' = ANY(skills)
   - Check experiences with word boundaries: experiences::text ~* '\mRAG\M'
   - Combine with OR: ('RAG' = ANY(skills) OR experiences::text ~* '\mRAG\M')
6. Word boundary regex ~* '\mTERM\M' avoids false matches (e.g., won't match "drag" when searching RAG)
7. For company/industry: experiences::text ILIKE '% term %'
8. Location: ILIKE for flexible matching
9. Always LIMIT 100
"""

EXAMPLE_QUERIES = """
EXAMPLE QUERIES:

Natural: "Find Python developers in San Francisco"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE 'python' = ANY(skills) AND location ILIKE '%San Francisco%' LIMIT 100;

Natural: "Senior engineers who worked at Google"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE seniority = 'Senior'
     AND experiences::text ILIKE '%Google%' LIMIT 100;

Natural: "Candidates with AI and machine learning skills"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE skills && ARRAY['AI', 'machine learning', 'ML'] LIMIT 100;

Natural: "Directors with startup experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE seniority = 'Director' AND worked_at_startup = true LIMIT 100;

Natural: "People who worked in fintech B2B companies"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE experiences @> '[{"business_model": "B2B"}]'::jsonb
     AND experiences::text ILIKE '%fintech%' LIMIT 100;

Natural: "Candidates with AI/ML industry experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE experiences::text ILIKE '%ai/ml%' LIMIT 100;

Natural: "Show me C-Level executives with 10+ years experience"
SQL: SELECT linkedin_url, name, location, seniority, years_experience, skills, headline, connected_to, worked_at_startup
     FROM candidates
     WHERE seniority = 'C-Level' AND years_experience >= 10 LIMIT 100;

Natural: "Find AI developers with RAG experience"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE (EXISTS (SELECT 1 FROM unnest(skills) s WHERE s ~* '\mAI\M|LLM|NLP|machine learning|ML\M')
            OR headline ~* '\mAI\M|LLM|NLP|machine learning|ML\M')
     AND ('RAG' = ANY(skills) OR experiences::text ~* '\mRAG\M') LIMIT 100;

Natural: "People who worked at Google"
SQL: SELECT linkedin_url, name, location, seniority, skills, headline, connected_to, years_experience, worked_at_startup
     FROM candidates
     WHERE experiences::text ILIKE '% Google %' LIMIT 100;
"""

def get_schema_context():
    """Return complete schema context for ChatGPT"""
    return DATABASE_SCHEMA + "\n" + EXAMPLE_QUERIES