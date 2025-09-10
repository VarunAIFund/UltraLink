import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
from contextlib import contextmanager

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:HvItNdUpgZBcIhRRMwhoXBbjgwkibQcF@shuttle.proxy.rlwy.net:48898/railway?sslmode=require')

def get_engine():
    """Create SQLAlchemy engine for database operations"""
    return create_engine(DATABASE_URL)

def get_session():
    """Create SQLAlchemy session for ORM operations"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

@contextmanager
def get_db_connection():
    """Context manager for raw psycopg2 database connections"""
    conn = None
    try:
        # Parse DATABASE_URL to get connection parameters
        if DATABASE_URL.startswith('postgresql://'):
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='superlever_candidates',
                user=os.getenv('DB_USER', os.getenv('USER'))  # Use system username
            )
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False