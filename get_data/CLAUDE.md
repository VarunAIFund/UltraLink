# CLAUDE.md - get_data Directory

This file provides guidance to Claude Code when working with the LinkedIn data scraping and processing pipeline in the `get_data` directory.

## Overview

The `get_data` directory contains the complete LinkedIn profile scraping and data quality pipeline. It handles connection data extraction, profile scraping via Apify, data validation, filtering, and preparation for cloud database migration.

## Directory Structure & Files

### **Core Scraping**
- `get_data.py` - Main Apify LinkedIn scraper with batch processing (200 profiles per batch)
- `connections_data/` - Directory containing CSV files with LinkedIn connection URLs
  - `linda_connections.csv` - Linda's LinkedIn connections URLs
  - `jon_connections.csv` - Jon's LinkedIn connections URLs

### **Data Processing & Quality**
- `evaluate_data_quality.py` - Comprehensive data quality assessment and field completeness analysis
- `validate_json_structure.py` - JSON structure validation ensuring all profiles have proper braces and formatting
- `filter_profiles.py` - Combined filtering script removing profiles with null fullName OR empty experiences
- `filter_incomplete_profiles.py` - Legacy filter for null fullName profiles only
- `filter_empty_experiences.py` - Legacy filter for empty experiences arrays only

### **Data Enhancement**
- `add_connection_source.py` - Adds `connected_to: ["name"]` field to track connection sources
- `reorder_json_fields.py` - Reorders JSON structure so `connected_to` appears after `followers` field

### **Utilities & Maintenance**
- `fix_json.py` - Repairs corrupted JSON files (missing brackets, syntax errors)

### **Cloud Migration Setup**
- `supabase_setup.py` - Full PostgreSQL connection setup with pgvector extension
- `supabase_simple_setup.py` - Simplified Supabase client setup approach
- `create_table_sql.sql` - SQL schema for LinkedIn profiles table with pgvector support

## Commands

### **Main Scraping Pipeline**
```bash
# Scrape LinkedIn profiles from CSV connections
python get_data.py                    # Processes linda_connections.csv by default

# For different connection sources, modify input_file in script:
# input_file = "connections_data/jon_connections.csv"
```

### **Data Quality Assessment**
```bash
# Evaluate data quality and completeness
python evaluate_data_quality.py      # Comprehensive field analysis and statistics

# Validate JSON structure integrity  
python validate_json_structure.py    # Ensures all profiles have proper JSON formatting
```

### **Data Filtering & Cleaning**
```bash
# Remove incomplete profiles (recommended)
python filter_profiles.py            # Combined filter: removes null fullName OR empty experiences

# Legacy individual filters
python filter_incomplete_profiles.py  # Remove profiles with null fullName only
python filter_empty_experiences.py   # Remove profiles with empty experiences only
```

### **Data Enhancement**
```bash
# Add connection tracking
python add_connection_source.py      # Adds connected_to field to all profiles

# Fix JSON structure ordering
python reorder_json_fields.py        # Moves connected_to field after followers
```

### **Maintenance & Repair**
```bash
# Fix corrupted JSON files
python fix_json.py                    # Repairs syntax errors, missing brackets

# Run multiple scraping batches
for i in {1..5}; do python get_data.py; done
```

### **Cloud Database Setup**
```bash
# Set up Supabase PostgreSQL database
python supabase_setup.py             # Full PostgreSQL connection setup
python supabase_simple_setup.py      # Alternative Supabase client approach

# Manual SQL execution (run in Supabase SQL Editor)
# Copy contents of create_table_sql.sql
```

## Data Flow Pipeline

### **LinkedIn Scraping Process**
```
CSV Connection URLs → Batch Processing → Apify Scraping → JSON Storage
        ↓                    ↓                ↓              ↓
linda_connections.csv → 200 URL batches → LinkedIn API → linda_connections.json
```

### **Quality Assessment Pipeline**
```
Raw JSON → Validation → Quality Analysis → Filtering → Enhanced JSON
    ↓          ↓            ↓              ↓           ↓
scraped.json → structure → completeness → clean data → production.json
```

### **Database Migration Pipeline**
```
Local JSON → Supabase Setup → Table Creation → Data Import → Cloud Database
     ↓            ↓              ↓             ↓            ↓
3,123 profiles → PostgreSQL → pgvector ready → bulk insert → production DB
```

## Key Features

### **Intelligent Batch Processing (`get_data.py`)**
- **Batch Size**: 200 LinkedIn URLs per Apify request
- **Duplicate Detection**: Checks existing results to avoid re-scraping
- **Connection Tracking**: Automatically adds `connected_to: ["name"]` field
- **Incremental Saving**: Appends new results to existing JSON files
- **Progress Reporting**: Shows batch completion status

### **Comprehensive Quality Analysis (`evaluate_data_quality.py`)**
- **Field Completeness**: Percentage fill rates for all profile fields
- **Experience Analysis**: Average experiences per profile, field completeness
- **Contact Information**: Email/phone coverage statistics
- **Company Data**: Unique companies and industries analysis
- **Duplicate Detection**: LinkedIn URL deduplication
- **Sample Records**: Examples of incomplete profiles for debugging

### **Robust Filtering System**
- **Combined Filtering**: Single script removes all incomplete profiles
- **Preservation**: Moves filtered profiles to separate files (not deleted)
- **Detailed Statistics**: Shows exactly what was filtered and why
- **Backup Creation**: Automatically creates backups before filtering

### **Cloud-Ready Architecture**
- **Supabase Integration**: Full PostgreSQL setup with pgvector for embeddings
- **Schema Design**: Optimized for LinkedIn profile data structure
- **Index Creation**: Performance indexes for common queries
- **Row Level Security**: Configurable access policies

## Data Structure

### **Input CSV Format**
```csv
First Name,Last Name,URL,Email Address,Company,Position,Connected On
John,Doe,https://www.linkedin.com/in/johndoe/,john@email.com,Company Inc,Engineer,Oct 15 2024
```

### **Output JSON Structure**
```json
{
  "linkedinUrl": "https://www.linkedin.com/in/profile",
  "fullName": "John Doe", 
  "headline": "Software Engineer at Company",
  "connections": 500,
  "followers": 1200,
  "connected_to": ["linda"],
  "experiences": [
    {
      "title": "Software Engineer",
      "subtitle": "Company Inc · Full-time",
      "companyLink1": "https://linkedin.com/company/company-inc"
    }
  ],
  "scraped_at": "2024-12-30T10:30:00.123456"
}
```

### **Database Schema (PostgreSQL)**
```sql
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    linkedin_url TEXT UNIQUE NOT NULL,
    full_name TEXT,
    headline TEXT,
    connections INTEGER,
    followers INTEGER, 
    connected_to TEXT[] DEFAULT '{}',
    experiences JSONB DEFAULT '[]',
    embedding vector(1536),  -- For future AI embeddings
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Environment Requirements

### **Required API Keys (.env)**
```env
APIFY_KEY=apify_api_xxxxxxxxxxxxx           # Apify LinkedIn scraper access
SUPABASE_URL=https://xxx.supabase.co        # Supabase project URL
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...  # Supabase anonymous key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJ...    # Supabase admin key
SUPABASE_DB_PASSWORD=your_db_password       # PostgreSQL password
```

### **Python Dependencies**
```bash
pip install apify-client python-dotenv supabase psycopg2-binary
```

## Data Quality Insights

### **Current Dataset Statistics** (3,123 profiles)
- **Success Rate**: 100% - All profiles structurally complete
- **Duplicates**: 0% - Perfect deduplication via LinkedIn URLs  
- **Field Completeness**:
  - `fullName`: 100% (3,123/3,123)
  - `headline`: ~95% coverage
  - `experiences`: 100% (non-empty arrays)
  - `email`: ~15% (due to LinkedIn privacy)
  - `connections`/`followers`: ~90% coverage

### **Processing Performance**
- **Batch Size**: 200 profiles optimal for Apify limits
- **Processing Speed**: ~30-60 seconds per 200-profile batch
- **Memory Usage**: Handles 3,123 profiles (~74MB JSON) efficiently
- **Error Recovery**: Robust handling of API failures and interruptions

## Troubleshooting

### **Common Issues**
1. **JSON Corruption**: Run `python fix_json.py` to repair syntax errors
2. **API Rate Limits**: Batch processing automatically handles Apify limits  
3. **Duplicate Scraping**: Existing URL detection prevents re-processing
4. **Connection Failures**: Check .env file credentials and network connectivity
5. **Large File Handling**: JSON files >50MB may need memory optimization

### **File Size Management**
- Current JSON file: ~74MB for 3,123 profiles
- Recommended batch processing for >10,000 profiles
- Cloud migration recommended for >100,000 profiles

## Migration Path

### **Current State**: Local JSON files
### **Next Steps**: 
1. Supabase PostgreSQL database
2. Vector embeddings for similarity search
3. AI enhancement pipeline integration
4. Production web application

The get_data directory provides a complete, production-ready LinkedIn data collection system with quality assurance, error recovery, and cloud migration capabilities.