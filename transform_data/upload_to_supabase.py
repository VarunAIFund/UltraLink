#!/usr/bin/env python3
"""
Upload structured LinkedIn profiles to Supabase

This script reads structured_profiles_test.json and uploads the data
to Supabase candidates table.

Usage:
    python upload_to_supabase.py
"""

import json
import os
import re
from typing import List, Dict, Any
from supabase_config import get_supabase_client

# Path to the JSON file
JSON_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    'structured_profiles_test.json'
)

def sanitize_string(value: Any) -> Any:
    """
    Remove null bytes and other problematic Unicode characters from strings.
    PostgreSQL cannot store null bytes (\u0000) in text fields.
    """
    if isinstance(value, str):
        # Remove null bytes and other control characters except newlines/tabs
        value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', value)
        return value
    elif isinstance(value, dict):
        return {k: sanitize_string(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_string(item) for item in value]
    else:
        return value

def load_profiles() -> List[Dict[str, Any]]:
    """
    Load profiles from JSON file
    """
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            print(f"✅ Loaded {len(profiles)} profiles from JSON file")
            return profiles
    except FileNotFoundError:
        print(f"❌ File not found: {JSON_FILE_PATH}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return []

def transform_profile_for_db(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform profile to match database schema and sanitize data
    """
    # Sanitize the entire profile to remove null bytes and problematic characters
    sanitized_profile = sanitize_string(profile)

    return {
        'linkedin_url': sanitized_profile.get('linkedinUrl'),
        'name': sanitized_profile.get('name'),
        'headline': sanitized_profile.get('headline'),
        'location': sanitized_profile.get('location'),
        'phone': sanitized_profile.get('phone'),
        'email': sanitized_profile.get('email'),
        'profile_pic': sanitized_profile.get('profilePic'),
        'profile_pic_high_quality': sanitized_profile.get('profilePicHighQuality'),
        'connected_to': sanitized_profile.get('connected_to', []),
        'seniority': sanitized_profile.get('seniority'),
        'skills': sanitized_profile.get('skills', []),
        'years_experience': sanitized_profile.get('years_experience'),
        'average_tenure': sanitized_profile.get('average_tenure'),
        'worked_at_startup': sanitized_profile.get('worked_at_startup', False),
        'experiences': sanitized_profile.get('experiences', []),  # Pass as Python object, Supabase handles JSONB conversion
        'education': sanitized_profile.get('education', [])  # Pass as Python object, Supabase handles JSONB conversion
    }

def create_table_if_not_exists():
    """
    Create the candidates table using the SQL migration file
    """
    try:
        print("📋 Creating candidates table...")

        # Read SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_candidates_table.sql')
        with open(sql_file_path, 'r') as f:
            sql = f.read()

        # Execute SQL using Supabase client
        client = get_supabase_client()

        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll need to use the REST API or PostgREST
        # For now, we'll skip this and assume table is created manually
        print("⚠️  Please run the SQL migration manually in Supabase SQL Editor:")
        print(f"   {sql_file_path}")
        print()

    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("Please create the table manually using the SQL file")

def upload_profiles(profiles: List[Dict[str, Any]], batch_size: int = 100):
    """
    Upload profiles to Supabase in batches
    """
    try:
        client = get_supabase_client()

        # Transform profiles for database
        db_profiles = [transform_profile_for_db(p) for p in profiles]

        # Filter out profiles without linkedin_url (required field)
        db_profiles = [p for p in db_profiles if p.get('linkedin_url')]

        print(f"📤 Uploading {len(db_profiles)} profiles to Supabase...")

        # Upload in batches
        total_uploaded = 0
        errors = []

        for i in range(0, len(db_profiles), batch_size):
            batch = db_profiles[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                # Use upsert to handle duplicates
                response = client.table('candidates').upsert(batch).execute()
                total_uploaded += len(batch)
                print(f"✅ Batch {batch_num}: Uploaded {len(batch)} profiles ({total_uploaded}/{len(db_profiles)})")

            except Exception as e:
                error_msg = f"Batch {batch_num} failed: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)

                # Try uploading one by one for this batch
                print(f"   Retrying batch {batch_num} one by one...")
                for profile in batch:
                    try:
                        client.table('candidates').upsert(profile).execute()
                        total_uploaded += 1
                        print(f"   ✅ Uploaded: {profile.get('name')}")
                    except Exception as e2:
                        error_msg = f"Failed to upload {profile.get('name')}: {str(e2)}"
                        print(f"   ❌ {error_msg}")
                        errors.append(error_msg)

        print(f"\n{'='*60}")
        print(f"📊 Upload Summary:")
        print(f"   Total profiles: {len(db_profiles)}")
        print(f"   Successfully uploaded: {total_uploaded}")
        print(f"   Errors: {len(errors)}")

        if errors:
            print(f"\n❌ Errors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors")

        return total_uploaded, errors

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 0, [str(e)]

def verify_upload():
    """
    Verify data was uploaded correctly
    """
    try:
        client = get_supabase_client()

        # Get count
        result = client.table('candidates').select('*', count='exact').limit(0).execute()
        count = result.count

        print(f"\n✅ Verification: Found {count} candidates in database")

        # Get a sample record
        sample = client.table('candidates').select('name, headline, seniority, linkedin_url').limit(3).execute()

        if sample.data:
            print(f"\n📋 Sample records:")
            for record in sample.data:
                print(f"   • {record['name']} - {record['seniority']} - {record['linkedin_url']}")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """
    Main execution
    """
    print("🚀 UltraLink - Supabase Upload")
    print("="*60)

    # Create table (show instructions)
    create_table_if_not_exists()

    # Load profiles
    profiles = load_profiles()
    if not profiles:
        print("❌ No profiles to upload")
        return

    # Upload profiles
    total, errors = upload_profiles(profiles)

    if total > 0:
        # Verify upload
        verify_upload()

    print("\n✅ Upload process complete!")

if __name__ == "__main__":
    main()
