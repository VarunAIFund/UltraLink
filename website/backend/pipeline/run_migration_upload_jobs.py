#!/usr/bin/env python3
"""
Run SQL migration to create upload_jobs table in Supabase
"""

import os
import psycopg2
from dotenv import load_dotenv
import urllib.parse

def run_migration():
    """
    Execute the SQL migration
    """
    try:
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

        # Read SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_upload_jobs_table.sql')
        with open(sql_file_path, 'r') as f:
            sql = f.read()

        print("📋 Running SQL migration for upload_jobs...")
        print("="*60)

        # Build connection string
        supabase_url = os.getenv('SUPABASE_URL')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        if not supabase_url or not db_password:
            print("❌ Missing SUPABASE_URL or SUPABASE_DB_PASSWORD in .env")
            return False

        # Extract project ref from URL
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        # URL encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(db_password)
        
        # Construct postgres connection string - use AWS-1 East as found working previously
        conn_string = f"postgresql://postgres.{project_ref}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

        print(f"Connecting to Supabase Postgres...")

        # Connect and execute
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Execute SQL
        cursor.execute(sql)
        conn.commit()

        print("✅ Migration executed successfully!")
        print()

        # Verify table was created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'upload_jobs';
        """)

        if cursor.fetchone():
            print(f"✅ Table 'upload_jobs' verified.")
        else:
            print("⚠️  Could not verify table creation")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()
