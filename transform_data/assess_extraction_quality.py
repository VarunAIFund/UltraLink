#!/usr/bin/env python3
"""
Assess Extraction Quality

GPT-5 powered assessment comparing raw vs transformed LinkedIn profile data quality.
Provides detailed quality scores and recommendations for improving AI transformation process.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = OpenAI()

# Load both files
with open('test_cleaned.json', 'r') as f:
    raw_data = json.load(f)

with open('structured_profiles.json', 'r') as f:
    processed_data = json.load(f)

# Create comparison for GPT
comparison_data = {
    "raw_data_sample": raw_data[:3],
    "processed_data_sample": processed_data[:3],
    "total_raw_records": len(raw_data),
    "total_processed_records": len(processed_data)
}

prompt = f"""
You are a data quality analyst. Compare the raw LinkedIn data with the AI-processed structured data and assess the extraction quality.

Raw Data (input): Contains original LinkedIn profile data from scraping
Processed Data (output): Contains AI-enhanced structured profiles

Here is the exact prompt that was used to transform the raw data:
\"\"\"
Based on the following candidate data, extract and infer the remaining profile information.
IMPORTANT: All output must be in English. If any content is in any other languages, translate it to English.

Please extract and return a JSON object with:
- name: Person's name
- headline: Professional headline or current role
- location: Location information standardized to "City, State/Province, Country" format. If any component is missing, include what's available. If remote work, use "Remote". If completely blank, leave blank.
- seniority: Seniority level (choose from: Intern, Entry, Junior, Mid, Senior, Lead, Manager, Director, VP, C-Level) based on titles and experience
- skills: List of all skills including programming languages inferred from experience descriptions
- years_experience: Total years of experience calculated from earliest date in work history up to current date
- worked_at_startup: Boolean indicating if they worked at startups. IMPORTANT: Consider the company's status at the TIME they worked there, not current status. Examples:
  * Google (founded 1998, IPO 2004): Anyone who worked there 1998-2004 = startup
- experiences: List of experience objects, one for each position in work history:
  * org: Organization name (extract from subtitle field, e.g., "Google · Full-time" -> "Google")
  * company_url: Company URL (extract from companyLink1 field)
  * title: Job title
  * summary: Job summary (extract from description text components in subComponents)
  * short_summary: Generate a standardized, descriptive text that summarizes this work experience in one or two sentences explaining the candidate's role and responsibilities in a narrative format.
  * location: Look at addressWithCountry field. If completely blank, leave blank. Position location standardized to "City, State/Province, Country" format. If any component is missing, include what's available. If remote work, use "Remote".
  * company_skills: List of technical and domain skills typically associated with working at this specific company based on experience description and implied skills (e.g., for Google: ["distributed systems", "machine learning", "cloud computing", "search algorithms"]; for Stripe: ["payments", "fintech", "API design", "financial systems"]; for Meta: ["social media", "advertising", "mobile development", "data analytics"]; for Pinecone: ["vector databases", "embeddings", "similarity search", "machine learning", "RAG", "AI infrastructure"])
  * business_model: Business model category (choose from: B2B, B2C, B2B2C, C2C, B2G) based on the company's primary business model
  * product_type: Product type category (choose from: Mobile App, Web App, Desktop App, SaaS, Platform, API/Developer Tools, E-commerce, Marketplace, Hardware, Consulting, Services) based on the company's primary product offering
  * industry_tags: List of relevant industry tags that describe the organization/role (e.g., "fintech", "healthcare", "edtech", "ecommerce", "saas", "ai/ml", etc.)
- education: List of education objects with properly cleaned information (from educations array):
  * school: Just the university/institution name (from title field)
  * degree: Just the degree level (from subtitle field)
  * field: The field of study (from subtitle field)

Note: 
- Skip career breaks or non-work experiences when creating positions
\"\"\"

Data to analyze:
{json.dumps(comparison_data, indent=2)}

Please provide a comprehensive quality assessment covering:

1. **Data Completeness**:
   - Are all important fields from raw data preserved in processed data?
   - What percentage of fields were successfully extracted/transformed?
   - Were any critical data points lost during processing?

2. **Data Accuracy**:
   - Do the processed fields accurately reflect the raw data?
   - Are company names, job titles, locations correctly extracted?
   - Are experience summaries accurate representations of the source?

3. **Data Enhancement**:
   - What new valuable information was added by AI processing?
   - How well did AI infer seniority levels, skills, business models?
   - Quality of generated summaries and classifications?

4. **Processing Success**:
   - Were all records successfully processed?
   - Any obvious processing errors or inconsistencies?
   - Overall success rate of the extraction pipeline?

5. **Areas for Improvement**:
   - What aspects of the extraction could be enhanced?
   - Any patterns in extraction failures or inaccuracies?
   - Recommendations for improving the AI processing?

Please provide specific examples from the data and actionable insights.

At the end, provide final scores (0-100) for each category:

**FINAL SCORES:**
- Data Completeness Score: X/100
- Data Accuracy Score: X/100  
- Data Enhancement Score: X/100
- Processing Success Score: X/100
- Overall Quality Score: X/100

Provide brief justification for each score.
"""

# Call GPT-5
response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": "You are an expert data quality analyst specializing in AI-powered data transformation assessment."},
        {"role": "user", "content": prompt}
    ]
)

# Output the result
print(response.choices[0].message.content)