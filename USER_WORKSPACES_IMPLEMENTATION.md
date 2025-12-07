# User Workspaces Implementation Guide

## Overview

Implement user-specific workspaces without authentication, using URL-based user identity. Users navigate to their workspace via URL (e.g., `/linda`, `/dan`) and get personalized search history and bookmarks.

**Key Feature:** This implementation includes a simple `users` table (username, display_name, email) to store user information in the database instead of hardcoding usernames. This provides:
- Professional display names ("Search Linda Smith's network" not "Search linda's network")
- Easy user management via SQL (no code changes needed to add/remove users)
- Auth-ready architecture (just add password_hash column later)
- Referential integrity via foreign keys
- Clean, minimal schema focused on essential fields only

**Status:** Email tracking feature is NOT part of this implementation. See "Future: Email Tracking" section for future reference.

---

## Goals

1. **User table** - Store users in database with display names, not hardcoded
2. **URL-based user identity** - `/linda` = Linda's workspace, `/dan` = Dan's workspace
3. **Professional UX** - Display "Linda Smith" not "linda" throughout interface
4. **Personalized search history** - Each user sees their own past searches
5. **Bookmarked candidates** - Users can star/save candidates for later
6. **Sidebar navigation** - Hamburger menu with "Searches" and "Bookmarks" links
7. **Easy user management** - Add users via SQL INSERT, not code changes
8. **No authentication** - Trust-based access via URLs (internal tool)
9. **Auth-ready architecture** - Just add password_hash column when ready (~1 hour)

---

## Route Structure

```
/                           → Default search (no user context, searches all connections)
/linda                      → Linda's workspace ("Search Linda's network...")
/linda/searches             → Linda's search history
/linda/bookmarks            → Linda's bookmarked candidates
/linda/search/abc-123       → Linda's specific search result

/dan                        → Dan's workspace
/dan/searches               → Dan's search history
/dan/bookmarks              → Dan's bookmarked candidates
... (same for jon, mary)
```

---

## Database Changes

### 1. Create `users` table

**Purpose:** Store user information and enable easy user management

```sql
-- Migration 1: Create users table
CREATE TABLE users (
    username TEXT PRIMARY KEY,           -- 'linda', 'dan', 'jon', 'mary'
    display_name TEXT NOT NULL,          -- 'Linda Smith', 'Dan Johnson'
    email TEXT                           -- 'linda@company.com'
);

-- Seed initial users
INSERT INTO users (username, display_name, email) VALUES
    ('linda', 'Linda Smith', 'linda@company.com'),
    ('dan', 'Dan Johnson', 'dan@company.com'),
    ('jon', 'Jon Lee', 'jon@company.com'),
    ('mary', 'Mary Wilson', 'mary@company.com');

-- Test query
SELECT username, display_name, email FROM users;
```

**Why a user table?**
- ✅ Display real names instead of usernames ("Search Linda Smith's network")
- ✅ Add new users via SQL instead of code changes
- ✅ Auth-ready: just add `password_hash` column later
- ✅ Referential integrity via foreign keys
- ✅ Store user email for future features

### 2. Add `user_name` to `search_sessions` table

**Purpose:** Track which user performed each search

```sql
-- Migration 2: Add user support to searches
ALTER TABLE search_sessions ADD COLUMN user_name TEXT;
CREATE INDEX idx_search_sessions_user_name ON search_sessions(user_name);

-- Add foreign key constraint
ALTER TABLE search_sessions
    ADD CONSTRAINT fk_search_user
    FOREIGN KEY (user_name) REFERENCES users(username);

-- Test query
SELECT id, query, user_name, created_at
FROM search_sessions
WHERE user_name = 'linda'
ORDER BY created_at DESC
LIMIT 10;
```

**Notes:**
- Existing searches will have `user_name = NULL` (searches from root `/`)
- New searches from `/linda` will have `user_name = 'linda'`
- Foreign key ensures only valid users can be referenced

### 3. Create `user_bookmarks` table

**Purpose:** Store user's bookmarked candidates

```sql
-- Migration 3: Create bookmarks table
CREATE TABLE user_bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name TEXT NOT NULL,
    linkedin_url TEXT NOT NULL,
    candidate_name TEXT,
    candidate_headline TEXT,
    bookmarked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    UNIQUE(user_name, linkedin_url)
);

CREATE INDEX idx_user_bookmarks_user_name ON user_bookmarks(user_name);
CREATE INDEX idx_user_bookmarks_created ON user_bookmarks(bookmarked_at DESC);

-- Add foreign key constraint
ALTER TABLE user_bookmarks
    ADD CONSTRAINT fk_bookmark_user
    FOREIGN KEY (user_name) REFERENCES users(username);

-- Test query
SELECT user_name, candidate_name, bookmarked_at
FROM user_bookmarks
WHERE user_name = 'linda'
ORDER BY bookmarked_at DESC;
```

**Schema Details:**
- `user_name` - User who bookmarked (references users table)
- `linkedin_url` - Primary identifier for candidate
- `candidate_name` - Cached for display (from candidates table)
- `candidate_headline` - Cached for display
- `notes` - Optional user notes about candidate
- `UNIQUE(user_name, linkedin_url)` - Prevents duplicate bookmarks
- Foreign key ensures only valid users can bookmark

---

## Backend Changes

**Organization:** User-related code is organized in a `users/` package (Python package with `__init__.py`) for better organization and scalability. This keeps all user operations (validation, future CRUD endpoints) in one place.

### File Structure

```
website/backend/
├── app.py                      # Add new endpoints here
├── save_search.py             # Update to accept user_name
├── bookmarks.py               # NEW FILE - Bookmark CRUD operations
├── users/                     # NEW FOLDER - User management package
│   ├── __init__.py            # NEW FILE - Package exports
│   ├── validation.py          # NEW FILE - User validation helpers
│   └── routes.py              # NEW FILE - Future user CRUD endpoints (optional)
└── requirements.txt           # No new dependencies needed
```

**Benefits of `users/` Package:**
- Clean organization: All user code in one place
- Scalable: Easy to add user CRUD endpoints later
- Standard Python package structure
- Clean imports: `from users import validate_user`

### 1. Create `users/` Package

**NEW FOLDER - Organize all user-related backend code**

#### `users/__init__.py`

**Purpose:** Export validation functions for clean imports

```python
"""
User management package
"""
from .validation import validate_user, get_all_users, get_db_connection

__all__ = ['validate_user', 'get_all_users', 'get_db_connection']
```

#### `users/validation.py`

**Purpose:** User validation helpers to replace hardcoded checks

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection (Railway vs local)"""
    is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
    password = os.getenv('SUPABASE_DB_PASSWORD')

    if is_railway:
        conn_string = f"postgresql://postgres:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    else:
        conn_string = f"postgresql://postgres:{password}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

    return psycopg2.connect(conn_string)


def validate_user(username):
    """
    Check if user exists

    Args:
        username: Username to validate

    Returns:
        dict: User info if valid, None if invalid
        {
            'username': 'linda',
            'display_name': 'Linda Smith',
            'email': 'linda@company.com'
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM users
            WHERE username = %s
        """, (username,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        return dict(user) if user else None
    except Exception as e:
        print(f"Error validating user: {e}")
        return None


def get_all_users():
    """
    Get all users

    Returns:
        list: Array of user objects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT username, display_name, email
            FROM users
            ORDER BY display_name
        """)

        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(user) for user in users]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
```

#### `users/routes.py` (Optional - For Future)

**Purpose:** Placeholder for future user CRUD endpoints

```python
"""
User CRUD operations (create, update, delete users via API)

Future endpoints:
- POST /admin/users - Create new user
- PUT /admin/users/<username> - Update user info
- DELETE /admin/users/<username> - Delete user
- PATCH /admin/users/<username>/password - Change password
"""

# TODO: Implement user management endpoints when needed
# For now, user management is done directly via SQL
```

**Note:** User management is currently done via SQL. This file is a placeholder for when you want API endpoints to manage users.

### 2. Update `save_search.py`

**Add `user_name` parameter to save function:**

```python
def save_search_session(query, connected_to, sql_query, results, total_results, total_cost, user_name=None):
    """
    Save search session to database

    Args:
        user_name: Optional user identifier (linda, dan, jon, mary)
    """
    search_id = str(uuid.uuid4())

    # Detect Railway vs local environment
    is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None

    if is_railway:
        conn_string = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD')}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    else:
        conn_string = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD')}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO search_sessions
            (id, query, connected_to, sql_query, results, total_results, total_cost, status, user_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            search_id,
            query,
            connected_to,
            sql_query,
            json.dumps(results),
            total_results,
            total_cost,
            'searching',
            user_name  # NEW FIELD
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return search_id
    except Exception as e:
        print(f"Error saving search session: {e}")
        return None
```

### 3. Update `app.py` - Search Endpoint

**Modify `/search-and-rank` to accept `user_name`:**

```python
from users import validate_user, get_all_users

@app.route('/search-and-rank', methods=['POST'])
def search_and_rank():
    try:
        data = request.json
        query = data.get('query', '')
        connected_to = data.get('connected_to', 'all')
        user_name = data.get('user_name')  # NEW: Optional user parameter

        # Validate user_name if provided (database lookup instead of hardcoded list)
        if user_name:
            user = validate_user(user_name)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or inactive user'
                }), 400

        # ... rest of existing search logic ...

        # When saving search, include user_name
        search_id = save_search_session(
            query=query,
            connected_to=connected_to_list,
            sql_query='',  # Updated later by background thread
            results=[],
            total_results=0,
            total_cost=0,
            user_name=user_name  # NEW PARAMETER
        )

        # ... rest of existing code ...

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 4. Create `bookmarks.py`

**NEW FILE - Bookmark CRUD operations:**

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_db_connection():
    """Get database connection (Railway vs local)"""
    is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
    password = os.getenv('SUPABASE_DB_PASSWORD')

    if is_railway:
        # Railway: Use connection pooler
        conn_string = f"postgresql://postgres:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    else:
        # Local: Direct connection
        conn_string = f"postgresql://postgres:{password}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

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
            result.append({
                'id': str(bookmark['id']),
                'user_name': bookmark['user_name'],
                'linkedin_url': bookmark['linkedin_url'],
                'bookmarked_at': bookmark['bookmarked_at'].isoformat(),
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
                    'profile_pic': bookmark['profile_pic']
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
```

### 5. Add User Management Endpoints to `app.py`

**Add these routes to `app.py`:**

```python
from users import validate_user, get_all_users

# Get all users
@app.route('/users', methods=['GET'])
def list_users():
    """Get all active users"""
    try:
        users = get_all_users()
        return jsonify({
            'success': True,
            'users': users,
            'total': len(users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Get specific user
@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    """Get user information"""
    try:
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': user
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 6. Add Search & Bookmark Endpoints to `app.py`

**Add these routes to `app.py`:**

```python
from bookmarks import add_bookmark, remove_bookmark, get_user_bookmarks, is_bookmarked
from users import validate_user

# Get user's searches
@app.route('/users/<username>/searches', methods=['GET'])
def get_user_searches(username):
    """Get all searches for a user"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username'
            }), 404

        is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None

        if is_railway:
            conn_string = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD')}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        else:
            conn_string = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD')}@aws-0-us-west-1.pooler.supabase.com:5432/postgres"

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, query, total_results, created_at, status
            FROM search_sessions
            WHERE user_name = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (username,))

        searches = []
        for row in cursor.fetchall():
            searches.append({
                'id': row[0],
                'query': row[1],
                'total_results': row[2],
                'created_at': row[3].isoformat(),
                'status': row[4]
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'searches': searches,
            'total': len(searches)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Add bookmark
@app.route('/users/<username>/bookmarks', methods=['POST'])
def add_user_bookmark(username):
    """Add a bookmark for a user"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username'
            }), 404

        data = request.json
        linkedin_url = data.get('linkedin_url')
        candidate_name = data.get('candidate_name')
        candidate_headline = data.get('candidate_headline')
        notes = data.get('notes')

        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'linkedin_url is required'
            }), 400

        result = add_bookmark(username, linkedin_url, candidate_name, candidate_headline, notes)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Remove bookmark
@app.route('/users/<username>/bookmarks/<path:linkedin_url>', methods=['DELETE'])
def remove_user_bookmark(username, linkedin_url):
    """Remove a bookmark"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username'
            }), 404

        result = remove_bookmark(username, linkedin_url)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Get bookmarks
@app.route('/users/<username>/bookmarks', methods=['GET'])
def get_user_bookmarks_endpoint(username):
    """Get all bookmarks for a user"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username'
            }), 404

        bookmarks = get_user_bookmarks(username)

        return jsonify({
            'success': True,
            'bookmarks': bookmarks,
            'total': len(bookmarks)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Check if bookmarked
@app.route('/users/<username>/bookmarks/check/<path:linkedin_url>', methods=['GET'])
def check_bookmark(username, linkedin_url):
    """Check if a candidate is bookmarked"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid username'
            }), 404

        bookmarked = is_bookmarked(username, linkedin_url)

        return jsonify({
            'success': True,
            'is_bookmarked': bookmarked
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## Frontend Changes

### File Structure

```
website/frontend/
├── app/
│   ├── page.tsx                    # Root search (no user context)
│   ├── [user]/                     # Dynamic user routes
│   │   ├── page.tsx               # User's search page
│   │   ├── searches/page.tsx      # Search history page
│   │   ├── bookmarks/page.tsx     # Bookmarks page
│   │   └── search/[id]/page.tsx   # Specific search (update from /search/[id])
│   └── layout.tsx                 # Root layout
│
├── components/
│   ├── HamburgerMenu.tsx          # NEW - Top-left hamburger button
│   ├── Sidebar.tsx                # NEW - Slide-out navigation
│   ├── CandidateCard.tsx          # UPDATE - Add bookmark star button
│   ├── SearchBar.tsx              # UPDATE - Show user context
│   └── SearchHistory.tsx          # NEW - Search list component
│
└── lib/
    └── api.ts                      # UPDATE - Add bookmark API functions
```

### 1. Create `components/HamburgerMenu.tsx`

**Hamburger button that opens sidebar:**

```tsx
'use client';

import { Menu } from 'lucide-react';
import { Button } from './ui/button';

interface HamburgerMenuProps {
  onOpen: () => void;
}

export default function HamburgerMenu({ onOpen }: HamburgerMenuProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onOpen}
      className="fixed top-4 left-4 z-40"
      aria-label="Open menu"
    >
      <Menu className="h-6 w-6" />
    </Button>
  );
}
```

### 2. Create `components/Sidebar.tsx`

**Slide-out navigation sidebar with display name:**

```tsx
'use client';

import { X, Search, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from './ui/button';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

export default function Sidebar({ isOpen, onClose, userName }: SidebarProps) {
  const [userDisplayName, setUserDisplayName] = useState(userName);

  // Fetch user info to get display name
  useEffect(() => {
    if (userName) {
      fetch(`${API_BASE_URL}/users/${userName}`)
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch(err => {
          console.error('Error fetching user info:', err);
        });
    }
  }, [userName]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 h-full w-80 bg-white dark:bg-gray-900 shadow-xl z-50 p-6"
          >
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="absolute top-4 right-4"
              aria-label="Close menu"
            >
              <X className="h-6 w-6" />
            </Button>

            {/* User display name */}
            <div className="mt-2 mb-8">
              <h2 className="text-2xl font-bold">{userDisplayName}</h2>
            </div>

            {/* Navigation links */}
            <nav className="space-y-4">
              <Link
                href={`/${userName}/searches`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <Search className="h-5 w-5" />
                <span className="text-lg">Searches</span>
              </Link>

              <Link
                href={`/${userName}/bookmarks`}
                onClick={onClose}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <Star className="h-5 w-5" />
                <span className="text-lg">Bookmarks</span>
              </Link>
            </nav>

            {/* Back to search */}
            <div className="absolute bottom-6 left-6 right-6">
              <Link
                href={`/${userName}`}
                onClick={onClose}
                className="block w-full p-3 text-center rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                Back to Search
              </Link>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 3. Update `components/SearchBar.tsx`

**Show user context in subtitle with display name:**

```tsx
import { useState, useEffect } from 'react';

interface SearchBarProps {
  userName?: string; // Optional user context
  // ... other props
}

export default function SearchBar({ userName, ...otherProps }: SearchBarProps) {
  const [userDisplayName, setUserDisplayName] = useState(userName);

  // Fetch user info to get display name
  useEffect(() => {
    if (userName) {
      fetch(`${API_BASE_URL}/users/${userName}`)
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setUserDisplayName(data.user.display_name);
          }
        })
        .catch(err => {
          console.error('Error fetching user info:', err);
        });
    }
  }, [userName]);

  return (
    <div className="text-center mb-8">
      <h1 className="text-4xl font-bold mb-2">🔗 UltraLink</h1>

      {userName ? (
        <p className="text-gray-600 dark:text-gray-400">
          Search {userDisplayName}'s network with natural language
        </p>
      ) : (
        <p className="text-gray-600 dark:text-gray-400">
          Search candidates with natural language
        </p>
      )}

      {/* Rest of search bar UI */}
    </div>
  );
}
```

### 4. Update `components/CandidateCard.tsx`

**Add bookmark star button:**

```tsx
'use client';

import { Star } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { addBookmark, removeBookmark, checkBookmark } from '@/lib/api';

interface CandidateCardProps {
  candidate: any;
  userName?: string; // Optional - only show bookmark if user context
  // ... other props
}

export default function CandidateCard({ candidate, userName, ...otherProps }: CandidateCardProps) {
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [loadingBookmark, setLoadingBookmark] = useState(false);

  // Check bookmark status on mount
  useEffect(() => {
    if (userName) {
      checkBookmarkStatus();
    }
  }, [userName, candidate.linkedin_url]);

  const checkBookmarkStatus = async () => {
    if (!userName) return;

    try {
      const result = await checkBookmark(userName, candidate.linkedin_url);
      setIsBookmarked(result.is_bookmarked);
    } catch (error) {
      console.error('Error checking bookmark:', error);
    }
  };

  const handleToggleBookmark = async () => {
    if (!userName) return;

    setLoadingBookmark(true);
    try {
      if (isBookmarked) {
        await removeBookmark(userName, candidate.linkedin_url);
        setIsBookmarked(false);
      } else {
        await addBookmark(userName, {
          linkedin_url: candidate.linkedin_url,
          candidate_name: candidate.name,
          candidate_headline: candidate.headline,
        });
        setIsBookmarked(true);
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
    } finally {
      setLoadingBookmark(false);
    }
  };

  return (
    <div className="candidate-card">
      {/* Existing card content */}

      {/* Bookmark button (only show if user context) */}
      {userName && (
        <Button
          variant="ghost"
          size="icon"
          onClick={handleToggleBookmark}
          disabled={loadingBookmark}
          className="absolute top-4 right-4"
          aria-label={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
        >
          <Star
            className={`h-5 w-5 ${
              isBookmarked ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'
            }`}
          />
        </Button>
      )}
    </div>
  );
}
```

### 5. Create `app/[user]/page.tsx`

**User's search page:**

```tsx
'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import SearchBar from '@/components/SearchBar';
import HamburgerMenu from '@/components/HamburgerMenu';
import Sidebar from '@/components/Sidebar';
import CandidateList from '@/components/CandidateList';

export default function UserSearchPage() {
  const params = useParams();
  const userName = params.user as string;

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchResults, setSearchResults] = useState([]);

  // Validate username
  const validUsers = ['linda', 'dan', 'jon', 'mary'];
  if (!validUsers.includes(userName?.toLowerCase())) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Invalid User</h1>
          <p className="text-gray-600">User "{userName}" not found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hamburger menu */}
      <HamburgerMenu onOpen={() => setIsSidebarOpen(true)} />

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        userName={userName}
      />

      {/* Main content */}
      <div className="container mx-auto px-4 py-8">
        <SearchBar
          userName={userName}
          onSearch={(results) => setSearchResults(results)}
        />

        {searchResults.length > 0 && (
          <CandidateList
            candidates={searchResults}
            userName={userName}
          />
        )}
      </div>
    </div>
  );
}
```

### 6. Create `app/[user]/searches/page.tsx`

**Search history page:**

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Search } from 'lucide-react';
import { getUserSearches } from '@/lib/api';
import HamburgerMenu from '@/components/HamburgerMenu';
import Sidebar from '@/components/Sidebar';

export default function SearchHistoryPage() {
  const params = useParams();
  const userName = params.user as string;

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSearches();
  }, [userName]);

  const loadSearches = async () => {
    setLoading(true);
    try {
      const result = await getUserSearches(userName);
      setSearches(result.searches);
    } catch (error) {
      console.error('Error loading searches:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <HamburgerMenu onOpen={() => setIsSidebarOpen(true)} />
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        userName={userName}
      />

      <div className="container mx-auto px-4 py-8 pl-20">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/${userName}`}
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Search
          </Link>
          <h1 className="text-3xl font-bold">Search History</h1>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading searches...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && searches.length === 0 && (
          <div className="text-center py-12">
            <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No searches yet</p>
          </div>
        )}

        {/* Searches list */}
        {!loading && searches.length > 0 && (
          <div className="space-y-4">
            {searches.map((search: any) => (
              <Link
                key={search.id}
                href={`/${userName}/search/${search.id}`}
                className="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-2">
                      {search.query}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {search.total_results} results •{' '}
                      {new Date(search.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {search.status === 'completed' && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                      Completed
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 7. Create `app/[user]/bookmarks/page.tsx`

**Bookmarks page:**

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Star } from 'lucide-react';
import { getUserBookmarks } from '@/lib/api';
import HamburgerMenu from '@/components/HamburgerMenu';
import Sidebar from '@/components/Sidebar';
import CandidateCard from '@/components/CandidateCard';

export default function BookmarksPage() {
  const params = useParams();
  const userName = params.user as string;

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBookmarks();
  }, [userName]);

  const loadBookmarks = async () => {
    setLoading(true);
    try {
      const result = await getUserBookmarks(userName);
      setBookmarks(result.bookmarks);
    } catch (error) {
      console.error('Error loading bookmarks:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <HamburgerMenu onOpen={() => setIsSidebarOpen(true)} />
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        userName={userName}
      />

      <div className="container mx-auto px-4 py-8 pl-20">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/${userName}`}
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Search
          </Link>
          <h1 className="text-3xl font-bold">Bookmarks</h1>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading bookmarks...</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && bookmarks.length === 0 && (
          <div className="text-center py-12">
            <Star className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No bookmarks yet</p>
          </div>
        )}

        {/* Bookmarks grid */}
        {!loading && bookmarks.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {bookmarks.map((bookmark: any) => (
              <CandidateCard
                key={bookmark.id}
                candidate={bookmark.candidate}
                userName={userName}
                onBookmarkRemoved={loadBookmarks}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 8. Move `app/search/[id]/page.tsx` to `app/[user]/search/[id]/page.tsx`

**Update search detail page to support user context:**

```tsx
// Copy existing app/search/[[...id]]/page.tsx content
// Update to read userName from params
// Pass userName to CandidateCard components

export default function SearchDetailPage() {
  const params = useParams();
  const searchId = params.id as string;
  const userName = params.user as string; // NEW: Read user from URL

  // ... existing logic ...

  return (
    <div>
      {userName && <HamburgerMenu onOpen={() => setIsSidebarOpen(true)} />}
      {userName && (
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          userName={userName}
        />
      )}

      <CandidateList
        candidates={candidates}
        userName={userName} // Pass to enable bookmark button
      />
    </div>
  );
}
```

### 9. Update `lib/api.ts`

**Add user and bookmark API functions:**

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Get all users
export async function getAllUsers() {
  const response = await fetch(`${API_BASE_URL}/users`);
  if (!response.ok) throw new Error('Failed to fetch users');
  return response.json();
}

// Get specific user
export async function getUser(userName: string) {
  const response = await fetch(`${API_BASE_URL}/users/${userName}`);
  if (!response.ok) throw new Error('Failed to fetch user');
  return response.json();
}

// Get user's searches
export async function getUserSearches(userName: string) {
  const response = await fetch(`${API_BASE_URL}/users/${userName}/searches`);
  if (!response.ok) throw new Error('Failed to fetch searches');
  return response.json();
}

// Get user's bookmarks
export async function getUserBookmarks(userName: string) {
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`);
  if (!response.ok) throw new Error('Failed to fetch bookmarks');
  return response.json();
}

// Add bookmark
export async function addBookmark(
  userName: string,
  data: {
    linkedin_url: string;
    candidate_name?: string;
    candidate_headline?: string;
    notes?: string;
  }
) {
  const response = await fetch(`${API_BASE_URL}/users/${userName}/bookmarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to add bookmark');
  return response.json();
}

// Remove bookmark
export async function removeBookmark(userName: string, linkedinUrl: string) {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(
    `${API_BASE_URL}/users/${userName}/bookmarks/${encodedUrl}`,
    { method: 'DELETE' }
  );
  if (!response.ok) throw new Error('Failed to remove bookmark');
  return response.json();
}

// Check if bookmarked
export async function checkBookmark(userName: string, linkedinUrl: string) {
  const encodedUrl = encodeURIComponent(linkedinUrl);
  const response = await fetch(
    `${API_BASE_URL}/users/${userName}/bookmarks/check/${encodedUrl}`
  );
  if (!response.ok) throw new Error('Failed to check bookmark');
  return response.json();
}
```

---

## Implementation Order

Follow this order to minimize debugging and ensure each piece works before moving to the next:

### Phase 1: Database Setup (20 min)
1. ✅ Run migration 1: Create `users` table and seed data
2. ✅ Run migration 2: Add `user_name` to `search_sessions` with foreign key
3. ✅ Run migration 3: Create `user_bookmarks` table with foreign key
4. ✅ Test queries manually in Supabase SQL editor

### Phase 2: Backend (75 min)
1. ✅ Create `users/` folder
2. ✅ Create `users/__init__.py` with exports
3. ✅ Create `users/validation.py` with validation helpers
4. ✅ (Optional) Create `users/routes.py` placeholder for future user CRUD
5. ✅ Create `bookmarks.py` with all CRUD functions
6. ✅ Update `save_search.py` to accept `user_name` parameter
7. ✅ Add 7 new routes to `app.py`:
   - `GET /users` (list all users)
   - `GET /users/<username>` (get user info)
   - `GET /users/<username>/searches`
   - `POST /users/<username>/bookmarks`
   - `GET /users/<username>/bookmarks`
   - `DELETE /users/<username>/bookmarks/<linkedin_url>`
   - `GET /users/<username>/bookmarks/check/<linkedin_url>`
8. ✅ Update `POST /search-and-rank` to accept optional `user_name`
9. ✅ Update imports: `from users import validate_user, get_all_users`
10. ✅ Replace all hardcoded validation with `validate_user()` calls
11. ✅ Test all endpoints with curl/Postman

### Phase 3: Frontend - Components (50 min)
1. ✅ Update `lib/api.ts` with user and bookmark API functions
2. ✅ Create `HamburgerMenu.tsx`
3. ✅ Create `Sidebar.tsx` with display name fetching
4. ✅ Update `SearchBar.tsx` to fetch and show display name
5. ✅ Update `CandidateCard.tsx` to add bookmark star button

### Phase 4: Frontend - Routing (60 min)
1. ✅ Create `app/[user]/page.tsx` (user search page)
2. ✅ Create `app/[user]/searches/page.tsx` (search history)
3. ✅ Create `app/[user]/bookmarks/page.tsx` (bookmarks)
4. ✅ Move/update `app/search/[id]/page.tsx` → `app/[user]/search/[id]/page.tsx`
5. ✅ Keep existing `app/page.tsx` as default (no user context)

### Phase 5: Testing (35 min)
1. ✅ Test root `/` (no user context, no hamburger, no bookmark buttons)
2. ✅ Test `/linda` (shows "Search Linda Smith's network", hamburger, bookmarks)
3. ✅ Test user display names appear in sidebar and subtitle
4. ✅ Test search → bookmark → view bookmarks → remove bookmark flow
5. ✅ Test search history page
6. ✅ Test sidebar navigation and animations
7. ✅ Test adding new user via SQL INSERT (verify appears immediately)
8. ✅ Test deleting user via SQL DELETE (verify removed from system)

**Total: ~4 hours**

---

## Testing Checklist

### Database Tests
- [ ] `users` table created with 4 initial users (username, display_name, email)
- [ ] `user_name` column added to `search_sessions` with foreign key
- [ ] `user_bookmarks` table created with foreign key
- [ ] Indexes created for performance
- [ ] Can insert/update/delete bookmarks
- [ ] Unique constraint works (can't bookmark same candidate twice)
- [ ] Foreign key prevents invalid user references
- [ ] Can add new user via SQL INSERT
- [ ] Can delete user when they leave (removes from database)

### Backend Tests
- [ ] `GET /users` returns all users
- [ ] `GET /users/linda` returns Linda's info with display_name
- [ ] `GET /users/invalid` returns 404
- [ ] `GET /users/linda/searches` returns Linda's searches
- [ ] `POST /users/linda/bookmarks` adds bookmark
- [ ] `GET /users/linda/bookmarks` returns bookmarks with full candidate data
- [ ] `DELETE /users/linda/bookmarks/{url}` removes bookmark
- [ ] `GET /users/linda/bookmarks/check/{url}` returns correct status
- [ ] `POST /search-and-rank` with `user_name` saves to database
- [ ] Invalid usernames return 404 error (not 400)
- [ ] validate_user() correctly checks database instead of hardcoded list
- [ ] Works on both Railway and local environments

### Frontend Tests
- [ ] Root `/` shows default search (no user context)
- [ ] `/linda` shows "Search Linda Smith's network with natural language" (display name!)
- [ ] Hamburger button appears on `/linda` but not `/`
- [ ] Sidebar opens/closes with smooth animation
- [ ] Sidebar shows display name ("Linda Smith" not "linda")
- [ ] Clicking "Searches" navigates to `/linda/searches`
- [ ] Clicking "Bookmarks" navigates to `/linda/bookmarks`
- [ ] Search history page loads Linda's searches
- [ ] Bookmarks page loads Linda's bookmarks
- [ ] Bookmark star button appears on candidate cards (when user context)
- [ ] Clicking star adds/removes bookmark
- [ ] Star is filled when bookmarked, empty when not
- [ ] Removing bookmark from bookmarks page refreshes list
- [ ] Adding new user via SQL makes them immediately accessible at `/{username}`

---

## Future: Email Tracking (NOT IMPLEMENTED YET)

### Database Schema

**Create `sent_emails` table:**

```sql
CREATE TABLE sent_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name TEXT NOT NULL,
    candidate_linkedin_url TEXT NOT NULL,
    candidate_name TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    sender_name TEXT NOT NULL,
    email_subject TEXT NOT NULL,
    email_body TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'sent',
    resend_email_id TEXT
);

CREATE INDEX idx_sent_emails_user_name ON sent_emails(user_name);
CREATE INDEX idx_sent_emails_candidate ON sent_emails(candidate_linkedin_url);
CREATE INDEX idx_sent_emails_sent_at ON sent_emails(sent_at DESC);
```

### Backend Changes

**Update `send_email.py` to save history:**

```python
def save_sent_email(user_name, candidate_linkedin_url, candidate_name,
                   recipient_name, recipient_email, sender_name,
                   email_subject, email_body, resend_email_id=None):
    """Save sent email to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sent_emails
            (user_name, candidate_linkedin_url, candidate_name,
             recipient_name, recipient_email, sender_name,
             email_subject, email_body, resend_email_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_name, candidate_linkedin_url, candidate_name,
              recipient_name, recipient_email, sender_name,
              email_subject, email_body, resend_email_id))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving sent email: {e}")

# Update send_intro_email endpoint to call save_sent_email after sending
```

**Add endpoint to get sent emails:**

```python
from users import validate_user

@app.route('/users/<username>/emails', methods=['GET'])
def get_user_emails(username):
    """Get all sent emails for a user"""
    try:
        # Validate username (database lookup)
        user = validate_user(username)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid username'}), 404

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id, candidate_name, candidate_linkedin_url,
                recipient_name, recipient_email, sender_name,
                email_subject, sent_at, status
            FROM sent_emails
            WHERE user_name = %s
            ORDER BY sent_at DESC
            LIMIT 100
        """, (username,))

        emails = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'emails': [dict(email) for email in emails],
            'total': len(emails)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Frontend Changes

**Add "Emails" link to sidebar:**

```tsx
// In Sidebar.tsx, add:
<Link
  href={`/${userName}/emails`}
  onClick={onClose}
  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100"
>
  <Mail className="h-5 w-5" />
  <span className="text-lg">Emails</span>
</Link>
```

**Create `app/[user]/emails/page.tsx`:**

```tsx
// Similar structure to searches/bookmarks pages
// Show list of sent emails with:
// - Candidate name
// - Sent to (recipient)
// - Subject line
// - Date sent
// - View email button (opens modal with full email body)
```

**Update `IntroductionEmailDialog.tsx`:**

```tsx
// After successful email send, pass user_name to backend
const response = await fetch('/send-intro-email', {
  method: 'POST',
  body: JSON.stringify({
    // ... existing fields ...
    user_name: userName, // NEW: Track who sent the email
  }),
});
```

---

## Auth Migration Path (Future)

**With the user table already in place, adding authentication is EXTREMELY EASY:**

### 1. Add password_hash column (2 min)

```sql
-- Add password hash column to users table
ALTER TABLE users ADD COLUMN password_hash TEXT;

-- Add password for users (use bcrypt to hash in production)
UPDATE users SET password_hash = '$2b$12$...' WHERE username = 'linda';
-- Repeat for other users
```

### 2. Backend Auth Middleware (10 min)

```python
from functools import wraps
import jwt
import bcrypt

SECRET_KEY = os.getenv('JWT_SECRET_KEY')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'error': 'No token provided'}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = payload['username']

            # Verify URL username matches token username
            url_user = kwargs.get('username')
            if url_user and url_user != request.user:
                return jsonify({'error': 'Unauthorized access'}), 403

        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

# Add to protected routes (ONE LINE per route):
@app.route('/users/<username>/searches')
@require_auth  # <-- Add this decorator
def get_user_searches(username):
    # Existing code unchanged!
```

### 3. Add Login Endpoint (10 min)

```python
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Validate credentials from database (not hardcoded!)
    user = validate_user(username)  # Already exists!
    if not user:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    # Check password hash
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result or not bcrypt.checkpw(password.encode(), result[0].encode()):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    # Generate JWT token
    token = jwt.encode({
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({
        'success': True,
        'token': token,
        'user': user  # Includes display_name, email, etc.
    })
```

### 3. Frontend Auth (30 min)

```typescript
// lib/auth.ts
export function setAuthToken(token: string) {
  localStorage.setItem('auth_token', token);
}

export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

export function clearAuthToken() {
  localStorage.removeItem('auth_token');
}

// lib/api.ts - Update all fetch calls
const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (response.status === 401) {
    // Token expired, redirect to login
    clearAuthToken();
    window.location.href = '/login';
  }

  return response;
};
```

### 4. Add Login Page (20 min)

```tsx
// app/login/page.tsx
export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    const response = await fetch('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();
    if (data.success) {
      setAuthToken(data.token);
      window.location.href = `/${username}`;
    }
  };

  return (
    <div>
      <input value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}
```

**Total auth migration time: ~1 hour** (even easier with user table!)

### Why It's So Easy:
- ✅ Simple user table already exists - just add password_hash column
- ✅ validate_user() function already written - reuse for login
- ✅ No schema refactoring needed - table design is auth-ready
- ✅ Display names already working throughout UI
- ✅ All endpoints already accept user context
- ✅ One SQL command + one decorator per route = done!

---

## Summary

### What You Get
1. **Simple user table** - Just 3 fields (username, display_name, email)
2. **User workspaces** - Linda, Dan, Jon, Mary each have their own URL
3. **Display names** - "Search Linda Smith's network" not "Search linda's network"
4. **Search history** - See past searches per user
5. **Bookmarks** - Star/save candidates for later
6. **Sidebar navigation** - Hamburger menu with smooth animations and display names
7. **Easy user management** - Add/remove users via SQL, not code changes
8. **No auth required** - Simple URL-based identity
9. **Auth-ready** - Can add JWT auth in ~1 hour (just add password_hash column!)

### Implementation Time
- **Database:** 20 min (3 migrations)
- **Backend:** 75 min (2 new files + updated validation)
- **Frontend:** 110 min (display name fetching)
- **Testing:** 35 min
- **Total:** ~4 hours

### Files Changed
- **Backend:** 6 files (create `users/` package with 3 files: `__init__.py`, `validation.py`, `routes.py`, plus `bookmarks.py`, plus updates to `app.py` and `save_search.py`)
- **Frontend:** 10 files (create 7 new, update 3 existing)
- **Database:** 3 migrations (users table, search_sessions, bookmarks)

### Difficulty
🟡 Medium - Requires Next.js routing knowledge and API integration

---

## Questions to Ask Before Starting

1. **Which environment to deploy first?** Local testing or directly to Railway?
2. **Color scheme for sidebar?** Match existing UltraLink brand colors?
3. **Initial user data?** Confirm usernames, display names, and emails:
   - linda → Linda Smith (linda@company.com)
   - dan → Dan Johnson (dan@company.com)
   - jon → Jon Lee (jon@company.com)
   - mary → Mary Wilson (mary@company.com)
4. **Bookmark notes?** Do users need to add notes when bookmarking, or just star/unstar?
5. **Search history limit?** Currently showing last 50 searches - is this enough?

---

## Next Steps

1. Run database migrations in Supabase SQL editor
2. Implement backend endpoints and test with curl
3. Create frontend components and pages
4. Test full user flow from search → bookmark → history
5. Deploy to Railway (backend env vars already set)

Good luck! 🚀
