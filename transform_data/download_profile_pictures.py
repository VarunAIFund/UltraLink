#!/usr/bin/env python3
"""
Download Profile Pictures

Downloads LinkedIn profile pictures locally and creates a mapping file.
Falls back to default image for expired or invalid URLs.
"""

import json
import os
import requests
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

# Configuration
INPUT_FILE = "structured_profiles_test.json"
OUTPUT_DIR = "profile_pictures"
MAPPING_FILE = "profile_picture_mapping.json"
DEFAULT_IMAGE = "default.jpg"
BATCH_SIZE = 50  # Concurrent downloads
TIMEOUT = 10  # seconds
MAX_RETRIES = 2

def sanitize_linkedin_url(linkedin_url):
    """Extract clean username from LinkedIn URL for filename"""
    if not linkedin_url:
        return "unknown"

    # Extract path from URL
    parsed = urlparse(linkedin_url)
    path = parsed.path.strip('/')

    # Extract username (last part after /in/)
    if '/in/' in path:
        username = path.split('/in/')[-1]
    else:
        username = path.replace('/', '-')

    # Clean filename
    username = username.replace('/', '-').replace('?', '').replace('&', '')

    return username

# Removed create_default_image() function - no longer needed
# Frontend shows HiUser icon for missing pictures

def download_image(linkedin_url, profile_pic_url, output_path, retries=MAX_RETRIES):
    """Download a single profile picture with retry logic"""

    for attempt in range(retries):
        try:
            # Download image
            response = requests.get(profile_pic_url, timeout=TIMEOUT, stream=True)

            if response.status_code == 200:
                # Save image
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return {
                    'status': 'success',
                    'error': None
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                if attempt < retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return {
                    'status': 'failed',
                    'error': error_msg
                }

        except requests.exceptions.Timeout:
            error_msg = "Timeout"
            if attempt < retries - 1:
                continue
            return {
                'status': 'failed',
                'error': error_msg
            }

        except Exception as e:
            error_msg = str(e)
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return {
                'status': 'failed',
                'error': error_msg
            }

    return {
        'status': 'failed',
        'error': 'Max retries exceeded'
    }

def process_profile(profile, default_image_path):
    """Process a single profile - download only, don't create default copies"""

    linkedin_url = profile.get('linkedinUrl')
    profile_pic_url = profile.get('profilePic')
    name = profile.get('name', 'Unknown')

    if not linkedin_url:
        return None

    # Generate filename
    username = sanitize_linkedin_url(linkedin_url)
    output_filename = f"{username}.jpg"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Skip if already exists
    if os.path.exists(output_path):
        return {
            'linkedin_url': linkedin_url,
            'local_path': output_path,
            'status': 'exists',
            'name': name
        }

    # Try to download
    if profile_pic_url:
        result = download_image(linkedin_url, profile_pic_url, output_path)

        if result['status'] == 'success':
            return {
                'linkedin_url': linkedin_url,
                'local_path': output_path,
                'status': 'success',
                'name': name,
                'downloaded_at': datetime.now().isoformat()
            }
        else:
            # Download failed - DON'T copy default, just return null
            # Frontend will show HiUser icon fallback
            return {
                'linkedin_url': linkedin_url,
                'local_path': None,
                'status': 'failed',
                'name': name,
                'error': result['error']
            }

    # No profile pic URL
    return {
        'linkedin_url': linkedin_url,
        'local_path': None,
        'status': 'no_image',
        'name': name,
        'error': 'No profile picture URL'
    }

def main():
    """Main download function"""

    print("📸 LinkedIn Profile Picture Downloader")
    print("=" * 60)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✅ Created output directory: {OUTPUT_DIR}")

    # No default image needed - frontend shows HiUser icon
    default_image_path = None

    # Load profiles
    print(f"\n📂 Loading profiles from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {INPUT_FILE}")
        return

    total_profiles = len(profiles)
    print(f"✅ Loaded {total_profiles:,} profiles")

    # Statistics
    stats = {
        'total': total_profiles,
        'success': 0,
        'default': 0,
        'exists': 0,
        'no_image': 0,
        'failed': 0
    }

    mapping = {}

    # Process profiles with thread pool
    print(f"\n⬇️  Downloading profile pictures (batch size: {BATCH_SIZE})...")
    print(f"⏱️  Timeout: {TIMEOUT}s, Retries: {MAX_RETRIES}")
    print()

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_profile, profile, default_image_path): profile
            for profile in profiles
        }

        # Process completed tasks
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()

            if result:
                status = result['status']
                stats[status] = stats.get(status, 0) + 1

                # Add to mapping
                mapping[result['linkedin_url']] = {
                    'local_path': result['local_path'],
                    'status': status,
                    'name': result['name']
                }

                if 'error' in result:
                    mapping[result['linkedin_url']]['error'] = result['error']

                if 'downloaded_at' in result:
                    mapping[result['linkedin_url']]['downloaded_at'] = result['downloaded_at']

            # Progress indicator
            if completed % 100 == 0 or completed == total_profiles:
                print(f"📈 Progress: {completed}/{total_profiles} ({completed/total_profiles*100:.1f}%)")

    # Save mapping file
    print(f"\n💾 Saving mapping file to {MAPPING_FILE}...")
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved mapping with {len(mapping):,} entries")

    # Display statistics
    print(f"\n📊 DOWNLOAD STATISTICS")
    print("=" * 60)
    print(f"Total profiles: {stats['total']:,}")
    print(f"✅ Successfully downloaded: {stats.get('success', 0):,}")
    print(f"📁 Already existed: {stats.get('exists', 0):,}")
    print(f"❌ Failed downloads: {stats.get('failed', 0):,}")
    print(f"❌ No profile picture URL: {stats.get('no_image', 0):,}")
    print(f"\n💡 Missing pictures will show HiUser icon in frontend")

    # Calculate storage
    total_size = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f))
        for f in os.listdir(OUTPUT_DIR)
        if os.path.isfile(os.path.join(OUTPUT_DIR, f))
    )
    size_mb = total_size / (1024 * 1024)

    print(f"\n💾 STORAGE")
    print("=" * 60)
    print(f"Total files: {len(os.listdir(OUTPUT_DIR)):,}")
    print(f"Total size: {size_mb:.2f} MB")
    print(f"Average size: {total_size/len(os.listdir(OUTPUT_DIR))/1024:.1f} KB per image")

    # Show sample mappings
    print(f"\n🔍 SAMPLE MAPPINGS (first 5):")
    print("=" * 60)
    for i, (url, data) in enumerate(list(mapping.items())[:5], 1):
        print(f"{i}. {data['name']}")
        print(f"   URL: {url}")
        print(f"   Path: {data['local_path']}")
        print(f"   Status: {data['status']}")
        if 'error' in data:
            print(f"   Error: {data['error']}")
        print()

    print("✅ Download complete!")
    print(f"\n📁 Profile pictures saved to: {OUTPUT_DIR}/")
    print(f"📄 Mapping file: {MAPPING_FILE}")

if __name__ == "__main__":
    main()
