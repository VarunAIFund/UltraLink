#!/usr/bin/env python3
"""
Import structured candidate profiles from JSON to PostgreSQL database.

This script reads structured_profiles.json and imports all candidate data
into the 3-table PostgreSQL schema (candidates, positions, education).
"""

import json
import sys
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import psycopg2.extras
from db_config import get_db_connection, test_connection

def convert_date_object(date_obj: Optional[Dict[str, int]]) -> Optional[date]:
    """Convert {year: 2024, month: 9} to Python date object"""
    if not date_obj or not isinstance(date_obj, dict):
        return None
    
    year = date_obj.get('year')
    month = date_obj.get('month')
    
    if year and month:
        # Use day 1 for start dates, last day for end dates
        return date(year, month, 1)
    return None

def prepare_candidate_data(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare candidate data for database insertion"""
    
    # Handle UUID fields - convert to UUID type or None
    def to_uuid(value):
        if value and isinstance(value, str):
            return value
        return None
    
    # Handle UUID arrays
    def to_uuid_array(value):
        if not value:
            return []
        if isinstance(value, list):
            return [uuid_str for uuid_str in value if uuid_str and isinstance(uuid_str, str)]
        return []
    
    return {
        'id': candidate.get('id'),
        'name': candidate.get('name'),
        'contact': to_uuid(candidate.get('contact')),
        'headline': candidate.get('headline'),
        'stage': candidate.get('stage'),
        'confidentiality': candidate.get('confidentiality'),
        'origin': candidate.get('origin'),
        'sourced_by': to_uuid(candidate.get('sourcedBy')),
        'owner': to_uuid(candidate.get('owner')),
        'archived': candidate.get('archived'),
        'is_anonymized': candidate.get('isAnonymized', False),
        'data_protection': candidate.get('dataProtection'),
        'location': candidate.get('location'),
        'emails': candidate.get('emails', []),
        'phones': json.dumps(candidate.get('phones', [])) if candidate.get('phones') else '[]',
        'links': candidate.get('links', []),
        'tags': candidate.get('tags', []),
        'sources': candidate.get('sources', []),
        'followers': to_uuid_array(candidate.get('followers', [])),
        'stage_changes': json.dumps(candidate.get('stageChanges', [])),
        'applications': json.dumps(candidate.get('applications', [])),
        'urls': json.dumps(candidate.get('urls', {})),
        'seniority': candidate.get('seniority'),
        'skills': candidate.get('skills', []),
        'years_experience': candidate.get('years_experience'),
        'average_tenure': candidate.get('average_tenure'),
        'worked_at_startup': candidate.get('worked_at_startup'),
        'created_at': candidate.get('createdAt'),
        'updated_at': candidate.get('updatedAt'),
        'last_interaction_at': candidate.get('lastInteractionAt'),
        'last_advanced_at': candidate.get('lastAdvancedAt'),
        'snoozed_until': candidate.get('snoozedUntil'),
        'raw_json': json.dumps(candidate)
    }

def prepare_positions_data(candidate_id: str, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare positions data for database insertion"""
    position_records = []
    
    for i, position in enumerate(positions):
        start_date = convert_date_object(position.get('start'))
        end_date = convert_date_object(position.get('end'))
        
        position_record = {
            'candidate_id': candidate_id,
            'vector_embedding': position.get('vector_embedding', ''),
            'org': position.get('org'),
            'title': position.get('title'),
            'summary': position.get('summary', ''),
            'short_summary': position.get('short_summary', ''),
            'location': position.get('location', ''),
            'start_date': start_date,
            'end_date': end_date,
            'start_json': json.dumps(position.get('start')),
            'end_json': json.dumps(position.get('end')),
            'position_order': i  # 0 = most recent
        }
        position_records.append(position_record)
    
    return position_records

def prepare_education_data(candidate_id: str, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare education data for database insertion"""
    education_records = []
    
    for edu in education:
        education_record = {
            'candidate_id': candidate_id,
            'school': edu.get('school'),
            'degree': edu.get('degree'),
            'field': edu.get('field')
        }
        education_records.append(education_record)
    
    return education_records

def insert_candidate_batch(cursor, candidates_data: List[Dict[str, Any]]):
    """Insert candidates one by one with proper type handling"""
    if not candidates_data:
        return
    
    # Insert candidates individually to handle type casting properly
    for candidate in candidates_data:
        try:
            cursor.execute("""
                INSERT INTO candidates (
                    id, name, contact, headline, stage, confidentiality, origin, sourced_by,
                    owner, archived, is_anonymized, data_protection, location, emails, phones,
                    links, tags, sources, followers, stage_changes, applications, urls,
                    seniority, skills, years_experience, worked_at_startup, created_at,
                    updated_at, last_interaction_at, last_advanced_at, snoozed_until, raw_json
                ) VALUES (
                    %s, %s, %s::uuid, %s, %s, %s, %s, %s::uuid,
                    %s::uuid, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s::uuid[], %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::jsonb
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = EXCLUDED.updated_at,
                    raw_json = EXCLUDED.raw_json
            """, (
                candidate['id'], candidate['name'], candidate['contact'], 
                candidate['headline'], candidate['stage'], candidate['confidentiality'],
                candidate['origin'], candidate['sourced_by'], candidate['owner'],
                candidate['archived'], candidate['is_anonymized'], candidate['data_protection'],
                candidate['location'], candidate['emails'], candidate['phones'],
                candidate['links'], candidate['tags'], candidate['sources'],
                candidate['followers'], candidate['stage_changes'], candidate['applications'],
                candidate['urls'], candidate['seniority'], candidate['skills'],
                candidate['years_experience'], candidate['worked_at_startup'],
                candidate['created_at'], candidate['updated_at'], candidate['last_interaction_at'],
                candidate['last_advanced_at'], candidate['snoozed_until'], candidate['raw_json']
            ))
        except Exception as e:
            print(f"❌ Error inserting candidate {candidate.get('id', 'unknown')}: {e}")
            raise e

def insert_positions_batch(cursor, positions_data: List[Dict[str, Any]]):
    """Insert positions with upsert logic - delete existing then insert new"""
    if not positions_data:
        return
    
    # Get unique candidate IDs from this batch
    candidate_ids = list(set(pos['candidate_id'] for pos in positions_data))
    
    # Delete existing positions for these candidates
    if candidate_ids:
        delete_sql = "DELETE FROM positions WHERE candidate_id = ANY(%s::uuid[])"
        cursor.execute(delete_sql, (candidate_ids,))
    
    # Insert new positions
    insert_sql = """
        INSERT INTO positions (
            candidate_id, vector_embedding, org, title, summary, short_summary,
            location, start_date, end_date, start_json, end_json, position_order
        ) VALUES %s
    """
    
    values = []
    for position in positions_data:
        values.append((
            position['candidate_id'], position['vector_embedding'], position['org'],
            position['title'], position['summary'], position['short_summary'],
            position['location'], position['start_date'], position['end_date'],
            position['start_json'], position['end_json'], position['position_order']
        ))
    
    psycopg2.extras.execute_values(
        cursor, insert_sql, values, template=None, page_size=100
    )

def insert_education_batch(cursor, education_data: List[Dict[str, Any]]):
    """Insert education with upsert logic - delete existing then insert new"""
    if not education_data:
        return
    
    # Get unique candidate IDs from this batch
    candidate_ids = list(set(edu['candidate_id'] for edu in education_data))
    
    # Delete existing education for these candidates
    if candidate_ids:
        delete_sql = "DELETE FROM education WHERE candidate_id = ANY(%s::uuid[])"
        cursor.execute(delete_sql, (candidate_ids,))
    
    # Insert new education records
    insert_sql = """
        INSERT INTO education (candidate_id, school, degree, field) 
        VALUES %s
    """
    
    values = []
    for edu in education_data:
        values.append((
            edu['candidate_id'], edu['school'], edu['degree'], edu['field']
        ))
    
    psycopg2.extras.execute_values(
        cursor, insert_sql, values, template=None, page_size=100
    )

def import_candidates_from_json(json_file_path: str):
    """Main function to import candidates from JSON file to database"""
    
    # Test database connection first
    if not test_connection():
        print("❌ Cannot connect to database. Please check your PostgreSQL setup.")
        return False
    
    # Load JSON data
    try:
        with open(json_file_path, 'r') as f:
            candidates = json.load(f)
        print(f"📁 Loaded {len(candidates)} candidates from {json_file_path}")
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return False
    
    # Process candidates in batches
    batch_size = 50
    total_candidates = len(candidates)
    successful_imports = 0
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Process in batches for better performance and memory usage
            for i in range(0, total_candidates, batch_size):
                batch = candidates[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_candidates + batch_size - 1) // batch_size
                
                print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} candidates)...")
                
                # Prepare data for this batch
                candidates_data = []
                all_positions_data = []
                all_education_data = []
                
                for candidate in batch:
                    try:
                        # Prepare candidate data
                        candidate_data = prepare_candidate_data(candidate)
                        candidates_data.append(candidate_data)
                        
                        # Prepare positions data
                        if candidate.get('positions'):
                            positions_data = prepare_positions_data(
                                candidate['id'], candidate['positions']
                            )
                            all_positions_data.extend(positions_data)
                        
                        # Prepare education data
                        if candidate.get('education'):
                            education_data = prepare_education_data(
                                candidate['id'], candidate['education']
                            )
                            all_education_data.extend(education_data)
                        
                        successful_imports += 1
                        
                    except Exception as e:
                        print(f"⚠️  Error processing candidate {candidate.get('id', 'unknown')}: {e}")
                        continue
                
                # Insert batch data
                try:
                    insert_candidate_batch(cursor, candidates_data)
                    insert_positions_batch(cursor, all_positions_data)
                    insert_education_batch(cursor, all_education_data)
                    
                    # Commit this batch
                    conn.commit()
                    print(f"✅ Batch {batch_num} completed successfully")
                    
                except Exception as e:
                    conn.rollback()
                    print(f"❌ Error inserting batch {batch_num}: {e}")
                    continue
        
        print(f"\n🎉 Import completed!")
        print(f"✅ Successfully imported: {successful_imports}/{total_candidates} candidates")
        
        # Show summary statistics
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM candidates")
            candidate_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM positions")
            position_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM education")
            education_count = cursor.fetchone()[0]
            
            print(f"\n📊 Database Summary:")
            print(f"   Candidates: {candidate_count:,}")
            print(f"   Positions: {position_count:,}")
            print(f"   Education: {education_count:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error during import: {e}")
        return False

if __name__ == "__main__":
    # Default to structured_profiles.json in same directory
    json_file = "structured_profiles.json"
    
    # Allow command line argument for different file
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    print(f"🚀 Starting import from {json_file}")
    success = import_candidates_from_json(json_file)
    
    if success:
        print("✅ Import completed successfully!")
        sys.exit(0)
    else:
        print("❌ Import failed!")
        sys.exit(1)