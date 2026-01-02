import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import quote_plus
from utils import generate_profile_pic_url

def get_db_connection():
    """Get database connection (Railway vs local)"""
    password = os.getenv('SUPABASE_DB_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')

    if not password:
        raise ValueError("SUPABASE_DB_PASSWORD environment variable is not set")
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is not set")

    # Extract project ID from Supabase URL
    project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
    encoded_password = quote_plus(password)

    # Always use connection pooler (port 6543) for better performance and stability
    conn_string = f"postgresql://postgres.{project_id}:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

    return psycopg2.connect(conn_string)


def add_bookmark(user_name, linkedin_url, candidate_name=None, candidate_headline=None, notes=None):
    """
    Add a bookmark for a user

    Args:
        user_name: User identifier (linda, dan, jon, mary)
        linkedin_url: LinkedIn URL of candidate
        candidate_name: Optional cached name
        candidate_headline: Optional cached headline
        notes: Optional user notes

    Returns:
        dict: {'success': bool, 'message': str, 'bookmark_id': str}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO user_bookmarks (user_name, linkedin_url, candidate_name, candidate_headline, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_name, linkedin_url) DO UPDATE
            SET notes = EXCLUDED.notes,
                candidate_name = EXCLUDED.candidate_name,
                candidate_headline = EXCLUDED.candidate_headline
            RETURNING id
        """, (user_name, linkedin_url, candidate_name, candidate_headline, notes))

        result = cursor.fetchone()
        bookmark_id = result['id']

        conn.commit()
        cursor.close()
        conn.close()

        return {
            'success': True,
            'message': 'Bookmark added successfully',
            'bookmark_id': str(bookmark_id)
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error adding bookmark: {str(e)}'
        }


def remove_bookmark(user_name, linkedin_url):
    """
    Remove a bookmark

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM user_bookmarks
            WHERE user_name = %s AND linkedin_url = %s
        """, (user_name, linkedin_url))

        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if deleted_count > 0:
            return {
                'success': True,
                'message': 'Bookmark removed successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Bookmark not found'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error removing bookmark: {str(e)}'
        }


def get_user_bookmarks(user_name):
    """
    Get all bookmarks for a user

    Returns:
        list: Array of bookmark objects with full candidate data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Join with candidates table to get full profile data
        cursor.execute("""
            SELECT
                b.id,
                b.user_name,
                b.linkedin_url,
                b.bookmarked_at,
                b.notes,
                c.name,
                c.headline,
                c.location,
                c.seniority,
                c.skills,
                c.years_experience,
                c.experiences,
                c.education,
                c.profile_pic
            FROM user_bookmarks b
            LEFT JOIN candidates c ON b.linkedin_url = c.linkedin_url
            WHERE b.user_name = %s
            ORDER BY b.bookmarked_at DESC
        """, (user_name,))

        bookmarks = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to list of dicts
        result = []
        for bookmark in bookmarks:
            # Generate profile pic URL from linkedin_url (like search results do)
            linkedin_url = bookmark['linkedin_url']
            profile_pic_url = generate_profile_pic_url(linkedin_url)
            
            result.append({
                'id': str(bookmark['id']),
                'user_name': bookmark['user_name'],
                'linkedin_url': linkedin_url,
                'bookmarked_at': bookmark['bookmarked_at'].isoformat() if bookmark['bookmarked_at'] else None,
                'notes': bookmark['notes'],
                'candidate': {
                    'name': bookmark['name'],
                    'headline': bookmark['headline'],
                    'location': bookmark['location'],
                    'seniority': bookmark['seniority'],
                    'skills': bookmark['skills'],
                    'years_experience': bookmark['years_experience'],
                    'experiences': bookmark['experiences'],
                    'education': bookmark['education'],
                    'profile_pic': profile_pic_url
                }
            })

        return result
    except Exception as e:
        print(f"Error getting bookmarks: {e}")
        return []


def is_bookmarked(user_name, linkedin_url):
    """
    Check if a candidate is bookmarked by a user

    Returns:
        bool: True if bookmarked, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM user_bookmarks
            WHERE user_name = %s AND linkedin_url = %s
        """, (user_name, linkedin_url))

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        return count > 0
    except Exception as e:
        print(f"Error checking bookmark: {e}")
        return False
