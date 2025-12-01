#!/usr/bin/env python3
"""
UltraLink Transform Data Pipeline Runner

Runs the complete data transformation pipeline in sequential order:
1. AI-powered profile transformation (GPT-5-nano)
2. Add Lever opportunities to profiles
3. Upload to Supabase database
4. Download profile pictures from LinkedIn
5. Upload profile pictures to Supabase Storage

Prerequisites:
- Run get_data pipeline to scrape LinkedIn profiles
- Ensure lever/linkedin_mapping_with_hired_status.json exists

Usage: python main.py
"""

import os
import sys
import gc
import subprocess

def clear_memory():
    """Clear Python memory to prevent glitches"""
    gc.collect()
    print("  💾 Memory cleared")

def run_step(step_num, step_name, command, description):
    """Run a pipeline step with memory management"""
    print(f"\n{step_name} Step {step_num}: {description}")
    print("-" * 60)

    # Run command and capture output
    result = subprocess.run(command, shell=True, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"  ❌ Step {step_num} failed with exit code {result.returncode}")
        print(f"  Stopping pipeline execution")
        sys.exit(1)

    print(f"  ✅ Step {step_num} completed")

    # Clear memory after step
    clear_memory()

def run_pipeline():
    """Run the complete transform_data pipeline"""

    print("=" * 60)
    print("🚀 UltraLink Transform Data Pipeline")
    print("=" * 60)
    print("\nThis pipeline will:")
    print("  1. AI-transform profiles with GPT-5-nano")
    print("  2. Add Lever opportunities to profiles")
    print("  3. Upload to Supabase database")
    print("  4. Download profile pictures from LinkedIn")
    print("  5. Upload profile pictures to Supabase Storage")
    print("\n" + "=" * 60)

    # Step 1: AI-powered transformation
    run_step(
        1,
        "🤖",
        "python3 transform.py",
        "AI transformation with GPT-5-nano"
    )
    # Uses OpenAI GPT-5-nano to transform cleaned profiles
    # Infers seniority, skills, years experience, business models, summaries
    # Output: structured_profiles_test.json

    # Step 2: Add Lever opportunities
    run_step(
        2,
        "📋",
        "python3 lever/add_lever_opportunities.py",
        "Adding Lever opportunities to profiles"
    )
    # Adds lever_opportunities field to each profile based on LinkedIn URL
    # Matches profiles with Lever hiring data (URLs and hired status)
    # Updates: structured_profiles_test.json

    # Step 3: Upload to Supabase
    run_step(
        3,
        "☁️",
        "python3 upload_to_supabase.py",
        "Uploading to Supabase database"
    )
    # Uploads structured profiles to Supabase PostgreSQL
    # Handles duplicates via linkedin_url primary key
    # Output: Database records in candidates table

    # Step 4: Download profile pictures
    run_step(
        4,
        "📥",
        "python3 download_profile_pictures.py --auto",
        "Downloading profile pictures from LinkedIn"
    )
    # Downloads profile pictures from LinkedIn
    # Skips already downloaded files for efficiency
    # Uses --auto flag to download all without prompting
    # Output: profile_pictures/ directory and profile_picture_mapping.json

    # Step 5: Upload profile pictures
    run_step(
        5,
        "📸",
        "python3 upload_pictures/upload_profile_pictures_to_supabase.py --auto",
        "Uploading profile pictures to Supabase Storage"
    )
    # Uploads downloaded profile pictures to Supabase Storage bucket
    # Skips already uploaded files for efficiency
    # Uses --auto flag to skip confirmation prompt
    # Output: Images in profile-pictures bucket

    # Final summary
    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)
    print("\n📁 Output:")
    print("  - structured_profiles_test.json (with lever_opportunities)")
    print("  - Supabase database updated with candidate profiles")
    print("  - profile_pictures/ directory with downloaded images")
    print("  - profile_picture_mapping.json (LinkedIn URL → local path)")
    print("  - Profile pictures uploaded to Supabase Storage bucket")
    print("\n🎯 Next steps:")
    print("  - Test search functionality: cd ../website/backend && python app.py")
    print("  - Run web app: cd ../website/frontend && npm run dev")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {e}")
        sys.exit(1)