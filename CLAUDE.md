# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

UltraLink is a LinkedIn profile data transformation and database import system that processes raw LinkedIn data scraped via Apify, transforms it using OpenAI's structured outputs, and imports it into a PostgreSQL database. The project follows a clear ETL (Extract, Transform, Load) pipeline.

## Commands

### Data Processing Pipeline

```bash
# 1. Clean raw Apify data (extract essential fields)
python clean_apify.py

# 2. Transform cleaned data using OpenAI structured outputs
python transform.py

# 3. Import structured profiles to PostgreSQL database
python import_to_db.py

# Generate data quality analysis report
python analyze_data_stats.py

# Test transformation on sample data
python test_transform.py
```

### Database Operations

```bash
# Test database connection
python -c "from db_config import test_connection; test_connection()"
```

## Architecture

### Data Flow Pipeline
```
Raw Apify Data → Clean → AI Transform → Database Import
     ↓              ↓           ↓            ↓
large_set.json → cleaned_apify.json → structured_profiles.json → PostgreSQL
```

### Core Components

1. **Data Cleaning (`clean_apify.py`)** - Extracts essential fields from complex Apify LinkedIn scraping data
2. **AI Transformation (`transform.py`)** - Uses OpenAI GPT-5-nano with structured parsing to infer profile information including seniority, skills, experience calculations, and startup employment history
3. **Database Import (`import_to_db.py`)** - Imports into PostgreSQL using 3-table normalized schema: `candidates`, `positions`, `education`

### Data Models

The system uses Pydantic models in `models.py`:
- `AIInferredProfile` - Main profile structure with name, location, seniority, skills, years_experience
- `Position` - Work experience with org, title, summary, location, industry_tags
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