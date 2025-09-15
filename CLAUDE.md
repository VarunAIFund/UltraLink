# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

UltraLink is a comprehensive LinkedIn data processing system with two main pipelines:
1. **Profile Pipeline**: Processes LinkedIn profile data and transforms it using OpenAI's structured outputs
2. **Company Pipeline**: Extracts and cleans LinkedIn company data for business intelligence

## Commands

### Profile Data Pipeline (transform_data directory)

```bash
# Main profile processing pipeline
python transform.py                # Transform LinkedIn profile data using OpenAI GPT-5-nano
python import_to_db.py            # Import structured profiles to PostgreSQL database
python analyze_data_stats.py      # Generate data quality analysis reports
python test_set.py               # Create test datasets from larger files

# Data cleaning and preparation
python clean_profiles.py         # Clean raw LinkedIn profile data
```

### Company Data Pipeline (transform_data directory)

```bash
# Company data processing
python extract_company_urls.py   # Extract unique company LinkedIn URLs from profile experiences
python clean_companies.py        # Clean company data from Apify scraping results

# Manual company data collection (when automated scraping is restricted)
python manual_linkedin_scraper.py   # Browser-assisted manual company data collection
```

### Database Operations

```bash
# Test database connection
python -c "from db_config import test_connection; test_connection()"
```

## Architecture

### Profile Data Flow Pipeline
```
LinkedIn Profile Data → AI Transform → Database Import → Analysis
        ↓                    ↓              ↓            ↓
   profile_data.json → structured_profiles.json → PostgreSQL → reports
```

### Company Data Flow Pipeline  
```
LinkedIn Profiles → Extract URLs → Manual Collection → Clean Data
       ↓                ↓               ↓              ↓
  experiences[] → company_urls.txt → manual_input → cleaned_companies.json
```

### Core Components

#### Profile Processing
1. **AI Transformation (`transform.py`)** - Uses OpenAI GPT-5-nano with structured parsing to transform LinkedIn profiles into standardized format with inferred seniority, skills, experience analysis, and startup employment history
2. **Database Import (`import_to_db.py`)** - Imports into PostgreSQL using 3-table normalized schema: `candidates`, `positions`, `education`
3. **Data Analysis (`analyze_data_stats.py`)** - Comprehensive data quality analysis and completeness reporting

#### Company Processing  
4. **URL Extraction (`extract_company_urls.py`)** - Extracts unique LinkedIn company URLs from profile experience data
5. **Company Cleaning (`clean_companies.py`)** - Processes and standardizes company data from Apify scraping results
6. **Manual Collection (`manual_linkedin_scraper.py`)** - Browser-assisted manual data collection for comprehensive company information

### Data Models

The system uses Pydantic models in `models.py`:
- `AIInferredProfile` - Main profile structure with name, location, seniority, skills, years_experience, experiences, education
- `Experience` - Work experience with vector_embedding, org, title, summary, short_summary, location, industry_tags  
- `Education` - Educational background with school, degree, field

### Database Configuration

- Primary database: PostgreSQL via Railway (configured in `db_config.py`)
- Fallback: Local PostgreSQL database `superlever_candidates`
- Connection management via SQLAlchemy and raw psycopg2 connections
- Environment variable: `DATABASE_URL` (defaults to Railway connection)

### Key Features

- **AI-Enhanced Processing**: Uses OpenAI structured outputs for intelligent data inference from job descriptions
- **LinkedIn URL as Primary Key**: Uses LinkedIn URLs as unique identifiers instead of UUIDs
- **Batch Processing**: Handles large datasets with incremental saving and error recovery
- **Data Quality Analysis**: Built-in completeness reporting (average 79.7% fill rate across 476 records)
- **Robust Error Handling**: Comprehensive exception management throughout the pipeline

### Input Data Structure

The system expects Apify LinkedIn scraping data with these key fields:
- `fullName`, `headline`, `linkedinUrl`, `email`, `mobileNumber`
- `addressWithCountry`, `experiences[]`, `educations[]`
- Nested experience objects with `title`, `subtitle`, `caption`, `metadata`, `subComponents[]`

### Environment Requirements

- OpenAI API access for GPT-5-nano model
- PostgreSQL database (Railway or local)
- Python packages: `openai`, `pydantic`, `psycopg2`, `sqlalchemy`, `python-dotenv`

### Data Quality Insights

Based on analysis of 476 records:
- 100% completeness: fullName, linkedinUrl
- 96.4% have work experience data (avg 4.7 positions per person)
- 95% have education data (avg 1.7 degrees per person)  
- 15.3% email coverage, 0% mobile numbers (privacy limitations)