#!/usr/bin/env python3
"""
UltraLink Transform Data Pipeline Runner

Runs the complete data transformation pipeline in sequential order:
1. Extract company URLs
2. Clean company data  
3. Clean profile data (with company enrichment)
4. AI-powered profile transformation
5. Data quality analysis
6. Database import

Usage: python main.py
"""

import os
import sys

def run_pipeline():
    """Run the complete transform_data pipeline"""
    
    print("🚀 Starting UltraLink Transform Data Pipeline")
    print("=" * 60)
    
    # Step 1: Extract company URLs from raw data
    print("\n📋 Step 1: Extracting company URLs...")
    os.system("python extract_company_urls.py")
    # Scans raw LinkedIn profiles to find unique company URLs from experience fields
    # Creates unique_company_linkedin_urls.txt with sorted list of company URLs
    
    # Step 2: Clean company data and add alternate URLs
    print("\n🏢 Step 2: Cleaning company data...")
    os.system("python clean_companies.py")
    # Cleans raw company data, keeps essential fields (name, industry, description)
    # Adds alternate numeric URLs from linkedin_redirects.csv for URL matching
    
    # Step 3: Clean profile data with company enrichment
    print("\n👥 Step 3: Cleaning and enriching profile data...")
    os.system("python clean_profiles.py")
    # Cleans raw profile data, keeps essential fields (name, contact, experiences, education)
    # Enriches experiences with company descriptions by matching URLs to cleaned company data
    
    # Step 4: AI-powered transformation using GPT-5-nano
    print("\n🤖 Step 4: AI transformation of profiles...")
    os.system("python transform.py")
    # Uses OpenAI GPT-5-nano to transform cleaned profiles into structured format
    # Infers seniority, skills, years experience, business models, industry tags, summaries
    
    # Step 5: Analyze data quality and completeness
    print("\n📊 Step 5: Analyzing data quality...")
    os.system("python analyze_data_stats.py")
    # Analyzes field completeness rates, generates data quality report
    # Creates comprehensive statistics on data coverage and distribution
    
    # Step 6: Import to PostgreSQL database
    #print("\n💾 Step 6: Importing to database...")
    #os.system("python import_to_db.py")
    
    print("\n✅ Pipeline completed successfully!")
    print("=" * 60)
    print("📁 Check output files:")
    print("  - unique_company_linkedin_urls.txt")
    print("  - more_companies_cleaned.json") 
    print("  - test_cleaned.json (or large_set_cleaned.json)")
    print("  - structured_profiles.json")
    print("  - data_analysis_report.txt")
    print("  - PostgreSQL database tables")

if __name__ == "__main__":
    run_pipeline()