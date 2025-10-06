#!/usr/bin/env python3
"""
Run SQL migration to create candidates table in Supabase

This script executes the SQL migration file to create the candidates table.
"""

import os
from supabase_config import get_supabase_client

def run_migration():
    """
    Execute the SQL migration
    """
    try:
        # Read SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_candidates_table.sql')
        with open(sql_file_path, 'r') as f:
            sql = f.read()

        print("📋 Running SQL migration...")
        print("="*60)

        # Get Supabase client
        client = get_supabase_client()

        # Execute SQL via RPC
        # Note: Supabase Python client doesn't support direct SQL execution
        # We need to use the PostgREST RPC or execute via psycopg2

        # Alternative: use psycopg2 to connect directly
        import psycopg2
        from dotenv import load_dotenv

        load_dotenv()

        # Build connection string
        supabase_url = os.getenv('SUPABASE_URL')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        # Extract project ref from URL (e.g., pcirzwgthuvbrbwvhwny from https://pcirzwgthuvbrbwvhwny.supabase.co)
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')

        # Construct postgres connection string
        # Format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
        conn_string = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

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
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'candidates'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()
        if columns:
            print(f"✅ Table 'candidates' created with {len(columns)} columns:")
            for col in columns[:10]:  # Show first 10 columns
                print(f"   - {col[1]} ({col[2]})")
            if len(columns) > 10:
                print(f"   ... and {len(columns) - 10} more columns")
        else:
            print("⚠️  Could not verify table creation")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("Alternative: Copy the SQL from create_candidates_table.sql")
        print("and run it in the Supabase SQL Editor at:")
        print(f"https://supabase.com/dashboard/project/{project_ref}/sql/new")
        return False

if __name__ == "__main__":
    run_migration()
