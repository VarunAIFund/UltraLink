#!/usr/bin/env python3
"""
Profile Picture Upload for CSV Pipeline

Downloads LinkedIn profile pictures and uploads them directly to Supabase Storage
(no local file storage - works on Railway container).
"""

import os
import sys
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform.supabase_config import get_supabase_client

# Configuration
BUCKET_NAME = 'profile-pictures'
TIMEOUT = 10  # seconds
MAX_RETRIES = 2
BATCH_SIZE = 50  # Concurrent downloads/uploads

def sanitize_linkedin_url_for_filename(linkedin_url):
    """Extract clean username from LinkedIn URL for filename"""
    if not linkedin_url:
        return "unknown"
    
    # Normalize
    url = linkedin_url.strip().rstrip('/').split('?')[0].split('#')[0].lower()
    
    # Extract path from URL
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Extract username (last part after /in/)
    if '/in/' in path:
        username = path.split('/in/')[-1]
    else:
        username = path.replace('/', '-')
    
    # Clean filename - remove any remaining special characters
    username = username.replace('/', '-').replace('?', '').replace('&', '').replace('=', '')
    
    return username

def download_and_upload_picture(linkedin_url, profile_pic_url, supabase):
    """
    Download profile picture from LinkedIn and upload directly to Supabase Storage
    
    Returns:
        dict: {'status': 'success'/'failed'/'no_image', 'filename': str, 'error': str}
    """
    if not profile_pic_url or profile_pic_url == '':
        return {
            'linkedin_url': linkedin_url,
            'status': 'no_image',
            'filename': None,
            'error': 'No profile picture URL'
        }
    
    # Generate filename from LinkedIn URL
    username = sanitize_linkedin_url_for_filename(linkedin_url)
    filename = f"{username}.jpg"
    
    # Try to download and upload
    for attempt in range(MAX_RETRIES):
        try:
            # Download image from LinkedIn
            response = requests.get(profile_pic_url, timeout=TIMEOUT, stream=True)
            
            if response.status_code == 200:
                # Read image data into memory
                image_data = response.content
                
                # Upload directly to Supabase Storage
                result = supabase.storage.from_(BUCKET_NAME).upload(
                    path=filename,
                    file=image_data,
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                
                # Check if upload was successful
                if hasattr(result, 'error') and result.error:
                    error_msg = f"Supabase upload error: {result.error}"
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return {
                        'linkedin_url': linkedin_url,
                        'status': 'failed',
                        'filename': filename,
                        'error': error_msg
                    }
                
                return {
                    'linkedin_url': linkedin_url,
                    'status': 'success',
                    'filename': filename,
                    'size': len(image_data),
                    'error': None
                }
            else:
                error_msg = f"LinkedIn returned HTTP {response.status_code}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return {
                    'linkedin_url': linkedin_url,
                    'status': 'failed',
                    'filename': filename,
                    'error': error_msg
                }
        
        except requests.exceptions.Timeout:
            error_msg = "Timeout downloading from LinkedIn"
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return {
                'linkedin_url': linkedin_url,
                'status': 'failed',
                'filename': filename,
                'error': error_msg
            }
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return {
                'linkedin_url': linkedin_url,
                'status': 'failed',
                'filename': filename,
                'error': error_msg
            }
    
    # If we get here, all retries failed
    return {
        'linkedin_url': linkedin_url,
        'status': 'failed',
        'filename': filename,
        'error': 'Max retries exceeded'
    }

def upload_profile_pictures_batch(profiles, log_func=print):
    """
    Download and upload profile pictures for a batch of profiles
    
    Args:
        profiles: List of profile dicts with 'linkedin_url', 'profile_pic', and optionally 'profile_pic_high_quality'
        log_func: Function to call for logging (default: print)
    
    Returns:
        dict: Summary with 'success', 'failed', 'no_image' counts and 'results' list
    """
    if not profiles or len(profiles) == 0:
        return {'success': 0, 'failed': 0, 'no_image': 0, 'results': []}
    
    log_func(f"Uploading profile pictures for {len(profiles)} profiles...")
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Process in parallel
    results = []
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Submit all tasks
        future_to_profile = {}
        for profile in profiles:
            linkedin_url = profile.get('linkedin_url')
            # Prefer high quality, fall back to standard
            profile_pic_url = profile.get('profile_pic_high_quality') or profile.get('profile_pic')
            
            future = executor.submit(
                download_and_upload_picture,
                linkedin_url,
                profile_pic_url,
                supabase
            )
            future_to_profile[future] = linkedin_url
        
        # Collect results as they complete
        for future in as_completed(future_to_profile):
            result = future.result()
            results.append(result)
            
            # Log progress
            if result['status'] == 'success':
                log_func(f"  ✓ Uploaded: {result['filename']}")
            elif result['status'] == 'no_image':
                log_func(f"  - Skipped: {result['linkedin_url']} (no profile picture)")
            else:
                log_func(f"  ✗ Failed: {result['linkedin_url']} - {result['error']}")
    
    # Count results
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    no_image_count = sum(1 for r in results if r['status'] == 'no_image')
    
    log_func(f"Profile picture upload complete: {success_count} success, {failed_count} failed, {no_image_count} no image")
    
    return {
        'success': success_count,
        'failed': failed_count,
        'no_image': no_image_count,
        'results': results
    }

if __name__ == "__main__":
    # Test with a sample profile
    test_profiles = [
        {
            'linkedin_url': 'https://www.linkedin.com/in/williamhgates',
            'profile_pic': 'https://media.licdn.com/dms/image/v2/C5603AQHv6LsdiUg1kw/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1633802270421?e=1745452800&v=beta&t=abc123',
            'profile_pic_high_quality': None
        }
    ]
    
    result = upload_profile_pictures_batch(test_profiles)
    print(f"\nTest result: {result}")
