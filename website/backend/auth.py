"""
Supabase token verification for the Flask backend.

Usage:
    from auth import require_auth, require_admin, get_request_user

    @app.route('/protected', methods=['POST'])
    def protected():
        user = get_request_user(request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        # user = {'email': 'varun@aifund.ai', 'id': 'uuid-...'}
"""

import os
import requests as http_requests
from typing import Optional
from flask import request, jsonify

SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')


def verify_supabase_token(token: str) -> Optional[dict]:
    """Verify a Supabase access token by calling Supabase's auth API.

    Returns {'email': str, 'id': str} on success, None if the token is
    missing, expired, or otherwise invalid.
    """
    if not token or not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        resp = http_requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                'Authorization': f'Bearer {token}',
                'apikey': SUPABASE_ANON_KEY,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {'email': data.get('email'), 'id': data.get('id')}
        return None
    except Exception as exc:
        print(f"[AUTH] Token verification error: {exc}")
        return None


def get_request_user(flask_request) -> Optional[dict]:
    """Extract and verify the Bearer token from a Flask request.

    Returns the verified user dict or None if unauthenticated.
    """
    auth_header = flask_request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:].strip()
    return verify_supabase_token(token)
