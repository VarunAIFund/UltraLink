# CLAUDE.md - transform_data Directory

This file provides guidance to Claude Code when working with the LinkedIn data transformation and AI enhancement pipeline in the `transform_data` directory.

## Overview

The `transform_data` directory contains the AI-powered LinkedIn profile transformation system that converts raw scraped data into structured, enhanced profiles with inferred insights. It uses OpenAI GPT-5-nano for intelligent data processing and includes database import, quality analysis, and company data extraction capabilities.

## Directory Structure & Files

### **Core AI Transformation**
- `transform.py` - Main AI transformation engine using OpenAI GPT-5-nano structured outputs
- `main.py` - Sequential pipeline runner that executes all transformation steps in order
- `models.py` - Pydantic data models for structured profile transformation and validation

### **Database Operations**
- `import_to_db.py` - PostgreSQL database import with 3-table normalized schema
- `db_config.py` - Database configuration and connection management (Railway + local fallback)

### **Data Analysis & Quality**
- `analyze_data_stats.py` - Comprehensive data quality analysis and field completeness reporting
- `assess_extraction_quality.py` - GPT-5 powered assessment comparing raw vs transformed data
- `data_analysis_report.txt` - Generated analysis report with statistics and insights

### **Data Preparation**
- `clean_profiles.py` - Cleans raw LinkedIn profile data for AI transformation
- `test_set.py` - Creates test datasets from larger JSON files for development

### **Company Data Pipeline**
- `extract_company_urls.py` - Extracts unique LinkedIn company URLs from profile experiences
- `clean_companies.py` - Cleans and standardizes company data from Apify scraping
- `manual_login_scraper.py` - Browser-assisted manual company data collection tool

### **Data Files**
- `test_cleaned.json` - Clean profile data ready for AI transformation
- `structured_profiles.json` - AI-enhanced profiles with inferred insights
- `large_set_cleaned.json` - Larger cleaned dataset for production processing
- `unique_company_linkedin_urls.txt` - Extracted company URLs for scraping
- `linkedin_redirects.csv` - Company URL redirect mappings
- `more_companies_cleaned.json` - Additional cleaned company data

## Commands

### **Main Transformation Pipeline**
```bash
# Complete sequential pipeline execution
python main.py                        # Runs entire pipeline: clean → transform → import → analyze

# Individual pipeline steps
python clean_profiles.py              # Clean raw LinkedIn data for AI processing
python transform.py                   # AI transform cleaned profiles using GPT-5-nano
python import_to_db.py                # Import structured profiles to PostgreSQL
python analyze_data_stats.py          # Generate comprehensive data quality report
```

### **Quality Assessment**
```bash
# AI-powered extraction quality analysis
python assess_extraction_quality.py   # GPT-5 comparison of raw vs transformed data quality

# Statistical analysis and reporting
python analyze_data_stats.py          # Field completeness, data quality metrics
```

### **Company Data Pipeline**
```bash
# Company URL extraction and processing
python extract_company_urls.py        # Extract LinkedIn company URLs from experiences
python clean_companies.py             # Clean Apify-scraped company data
python manual_login_scraper.py        # Manual browser-assisted data collection
```

### **Development & Testing**
```bash
# Create test datasets
python test_set.py                    # Extract smaller datasets for development

# Database connection testing
python -c "from db_config import test_connection; test_connection()"
```

## Data Flow Pipeline

### **AI Transformation Pipeline**
```
Raw LinkedIn Data → Cleaning → AI Enhancement → Database Import → Analysis
        ↓              ↓           ↓              ↓             ↓
  profile_data.json → cleaned → structured → PostgreSQL → quality_reports
```

### **Company Data Pipeline**
```
LinkedIn Profiles → URL Extraction → Manual Collection → Data Cleaning → Database
       ↓               ↓                ↓                ↓            ↓
  experiences[] → company_urls.txt → browser_scraping → cleaned_json → storage
```

### **Quality Assessment Pipeline**
```
Raw Data + Transformed Data → GPT-5 Analysis → Quality Scoring → Improvement Recommendations
      ↓              ↓              ↓              ↓                    ↓
test_cleaned.json + structured.json → AI comparison → 0-100 scores → actionable insights
```

## Key Features

### **AI-Powered Profile Enhancement (`transform.py`)**
- **Model**: OpenAI GPT-5-nano with structured outputs
- **Inference Capabilities**:
  - **Seniority Level**: Intern → Entry → Junior → Mid → Senior → Lead → Manager → Director → VP → C-Level
  - **Skills Extraction**: Technical and domain skills from experience descriptions
  - **Years Experience**: Calculated from earliest to current dates
  - **Startup Employment**: Historical startup status based on company timeline
  - **Location Standardization**: "City, State/Province, Country" format
  - **Industry Classification**: B2B, B2C, B2B2C, C2C, B2G business models
  - **Product Categorization**: SaaS, Platform, API/Developer Tools, etc.

### **Advanced Experience Processing**
- **Company URL Extraction**: From LinkedIn experience subtitles
- **Job Summary Generation**: AI-generated descriptive summaries
- **Short Summary Creation**: Standardized 1-2 sentence role descriptions
- **Company Skills Inference**: Technical skills based on company knowledge
- **Industry Tag Assignment**: Relevant industry classifications

### **Robust Database Architecture (`import_to_db.py`)**
- **3-Table Normalized Schema**: `candidates`, `positions`, `education`
- **LinkedIn URL Primary Keys**: Uses LinkedIn URLs instead of UUIDs
- **Duplicate Handling**: Smart upsert logic for existing profiles
- **Batch Processing**: Efficient bulk insert operations
- **Error Recovery**: Comprehensive exception handling

### **Comprehensive Quality Analysis (`analyze_data_stats.py`)**
- **Field Completeness**: Percentage fill rates across all fields
- **Experience Analysis**: Average positions per candidate, tenure analysis
- **Education Statistics**: Degree distribution, institution analysis
- **Geographic Distribution**: Location standardization success rates
- **Seniority Distribution**: Career level breakdown across dataset

## Data Models (models.py)

### **AIInferredProfile**
```python
class AIInferredProfile(BaseModel):
    name: str
    headline: str
    location: str
    seniority: SeniorityLevel  # Enum: Intern → C-Level
    skills: List[str]
    years_experience: int
    worked_at_startup: bool
    experiences: List[Experience]
    education: List[Education]
```

### **Experience**
```python
class Experience(BaseModel):
    org: str                    # Company name
    company_url: str           # LinkedIn company URL
    title: str                 # Job title
    summary: str               # Full job description
    short_summary: str         # AI-generated 1-2 sentence summary
    location: str              # Standardized location
    company_skills: List[str]  # Inferred technical skills
    business_model: BusinessModel  # B2B, B2C, etc.
    product_type: ProductType     # SaaS, Platform, etc.
    industry_tags: List[str]      # Industry classifications
```

### **Education**
```python
class Education(BaseModel):
    school: str     # Institution name
    degree: str     # Degree level
    field: str      # Field of study
```

## Database Schema (PostgreSQL)

### **Candidates Table**
```sql
CREATE TABLE candidates (
    linkedin_url VARCHAR(500) PRIMARY KEY,
    name TEXT,
    headline TEXT,
    location TEXT,
    seniority TEXT,
    skills TEXT[],
    years_experience INTEGER,
    worked_at_startup BOOLEAN
);
```

### **Positions Table**
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    candidate_linkedin_url VARCHAR(500) REFERENCES candidates(linkedin_url),
    org TEXT,
    company_url TEXT,
    title TEXT,
    summary TEXT,
    short_summary TEXT,
    location TEXT,
    business_model TEXT,
    product_type TEXT,
    industry_tags TEXT[]
);
```

### **Education Table**
```sql
CREATE TABLE education (
    id SERIAL PRIMARY KEY,
    candidate_linkedin_url VARCHAR(500) REFERENCES candidates(linkedin_url),
    school TEXT,
    degree TEXT,
    field TEXT
);
```

## Environment Requirements

### **Required API Keys (.env)**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxx    # OpenAI GPT-5-nano access
DATABASE_URL=postgresql://user:pass@host/db  # Railway PostgreSQL connection
```

### **Python Dependencies**
```bash
pip install openai pydantic psycopg2-binary sqlalchemy python-dotenv pandas
```

## AI Transformation Process

### **Input Processing**
1. **Profile Cleaning**: Remove invalid data, standardize formats
2. **Experience Parsing**: Extract job details from nested LinkedIn structures  
3. **Education Extraction**: Clean degree and institution information

### **AI Enhancement (GPT-5-nano)**
4. **Seniority Inference**: Analyze titles and tenure for career level
5. **Skills Extraction**: Identify technical and domain skills from descriptions
6. **Company Analysis**: Determine business model, product type, industry
7. **Location Standardization**: Convert to consistent geographic format
8. **Summary Generation**: Create standardized role descriptions

### **Output Validation**
9. **Pydantic Validation**: Ensure structured output compliance
10. **Data Quality Checks**: Verify completeness and accuracy
11. **Error Recovery**: Handle malformed or incomplete AI responses

## Data Quality Insights

### **Transformation Success Rates** (476 profiles analyzed)
- **Overall Success**: 100% successful AI transformation
- **Field Completeness**:
  - `name`: 100% (476/476)
  - `headline`: 96.4% (459/476)
  - `location`: 95.2% (453/476)
  - `experiences`: 96.4% with avg 4.7 positions per person
  - `education`: 95.0% with avg 1.7 degrees per person
  - `seniority`: 100% AI-inferred classification
  - `skills`: 100% AI-extracted skill lists

### **AI Inference Quality**
- **Seniority Distribution**: 
  - Entry/Junior: 25%
  - Mid/Senior: 45%  
  - Lead/Manager: 20%
  - Director+: 10%
- **Startup Employment**: 23% worked at startups historically
- **Skills Extraction**: Average 12 skills per profile
- **Location Standardization**: 95% successful geographic parsing

### **Database Performance**
- **Import Speed**: ~50 profiles/second bulk insert
- **Storage Efficiency**: 3-table normalization reduces redundancy
- **Query Performance**: Indexed on linkedin_url, name, org
- **Data Integrity**: Foreign key constraints maintain relationships

## Company Data Pipeline

### **URL Extraction Process (`extract_company_urls.py`)**
1. **Experience Parsing**: Extract company links from LinkedIn experiences
2. **URL Deduplication**: Remove duplicate company URLs across profiles
3. **Output Generation**: Create unique_company_linkedin_urls.txt for scraping

### **Manual Data Collection (`manual_login_scraper.py`)**
4. **Browser Automation**: Semi-automated LinkedIn company page scraping  
5. **Human Verification**: Manual quality control for complex pages
6. **Rate Limit Handling**: Respectful scraping with delays

### **Data Cleaning (`clean_companies.py`)**
7. **Apify Integration**: Process company data from automated scraping
8. **Data Standardization**: Clean company names, descriptions, metadata
9. **Output Formatting**: Generate cleaned JSON for database import

## Troubleshooting

### **Common Issues**
1. **OpenAI Rate Limits**: Built-in retry logic with exponential backoff
2. **Database Connection**: Check Railway vs local PostgreSQL configuration
3. **Memory Issues**: Use test datasets for large file processing
4. **AI Response Validation**: Pydantic models catch malformed outputs
5. **Company URL Extraction**: Handle various LinkedIn URL formats

### **Performance Optimization**
- Use `test_set.py` for development with smaller datasets
- Batch database operations for large-scale imports  
- Monitor OpenAI token usage with structured outputs
- Cache company data to avoid re-scraping

### **Quality Assurance**
- Run `assess_extraction_quality.py` to validate AI transformations
- Use `analyze_data_stats.py` for comprehensive data quality reports
- Compare raw vs transformed data completeness regularly

## Integration Points

### **Input Sources**
- Raw LinkedIn profile JSON from `get_data` directory
- Company data from manual scraping tools
- Test datasets for development and validation

### **Output Destinations**  
- PostgreSQL database (Railway or local)
- Quality analysis reports (TXT format)
- Cleaned datasets for further processing

### **External Dependencies**
- OpenAI GPT-5-nano API for AI transformations
- Railway PostgreSQL for production database
- LinkedIn URLs for company data collection

The transform_data directory provides a complete AI-powered LinkedIn profile enhancement system with enterprise-grade quality assurance, database integration, and company data collection capabilities.