#!/usr/bin/env python3
"""
Download Profile Pictures

Downloads LinkedIn profile pictures locally and creates a mapping file.
Falls back to default image for expired or invalid URLs.

Usage:
    python download_profile_pictures.py          # Interactive mode (asks how many to download)
    python download_profile_pictures.py --auto   # Auto mode (downloads all profiles)
"""

import json
import os
import sys
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

def normalize_linkedin_url(linkedin_url):
    """Normalize LinkedIn URL for consistent comparison"""
    if not linkedin_url:
        return None

    # Remove trailing slash, query params, fragments
    url = linkedin_url.strip().rstrip('/').split('?')[0].split('#')[0]

    # Convert to lowercase for consistency
    return url.lower()

def sanitize_linkedin_url(linkedin_url):
    """Extract clean username from LinkedIn URL for filename"""
    if not linkedin_url:
        return "unknown"

    # Normalize first
    normalized = normalize_linkedin_url(linkedin_url)
    if not normalized:
        return "unknown"

    # Extract path from URL
    parsed = urlparse(normalized)
    path = parsed.path.strip('/')

    # Extract username (last part after /in/)
    if '/in/' in path:
        username = path.split('/in/')[-1]
    else:
        username = path.replace('/', '-')

    # Clean filename - remove any remaining special characters
    username = username.replace('/', '-').replace('?', '').replace('&', '').replace('=', '')

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

def is_valid_image(filepath):
    """Check if image file is valid (not corrupted/empty)"""
    try:
        if not os.path.exists(filepath):
            return False

        # Check file size (should be at least 1KB)
        size = os.path.getsize(filepath)
        if size < 1024:
            return False

        # File exists and has reasonable size
        return True
    except Exception:
        return False

def process_profile(profile, default_image_path, existing_mapping):
    """Process a single profile - download only, don't create default copies"""

    linkedin_url = profile.get('linkedinUrl')
    profile_pic_url = profile.get('profilePic')
    name = profile.get('name', 'Unknown')

    if not linkedin_url:
        return None

    # Normalize URL for consistent lookup
    normalized_url = normalize_linkedin_url(linkedin_url)

    # Check if already in mapping with successful download
    if normalized_url in existing_mapping:
        existing_entry = existing_mapping[normalized_url]
        if existing_entry.get('status') == 'success' and existing_entry.get('local_path'):
            # Verify the file still exists and is valid
            if is_valid_image(existing_entry['local_path']):
                return {
                    'linkedin_url': linkedin_url,
                    'local_path': existing_entry['local_path'],
                    'status': 'skipped_mapping',
                    'name': name
                }

    # Generate filename
    username = sanitize_linkedin_url(linkedin_url)
    output_filename = f"{username}.jpg"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Check if file exists and is valid
    if os.path.exists(output_path):
        if is_valid_image(output_path):
            return {
                'linkedin_url': linkedin_url,
                'local_path': output_path,
                'status': 'skipped_filesystem',
                'name': name
            }
        else:
            # File exists but is invalid - delete and re-download
            print(f"   ⚠️  Invalid image found for {name}, re-downloading...")
            try:
                os.remove(output_path)
            except Exception:
                pass

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

    # Check for --auto flag
    auto_mode = '--auto' in sys.argv

    print("📸 LinkedIn Profile Picture Downloader")
    print("=" * 60)

    if auto_mode:
        print("🤖 Running in AUTO mode (will download all profiles)")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✅ Created output directory: {OUTPUT_DIR}")

    # No default image needed - frontend shows HiUser icon
    default_image_path = None

    # Load existing mapping file if available
    existing_mapping = {}
    if os.path.exists(MAPPING_FILE):
        print(f"\n📄 Loading existing mapping from {MAPPING_FILE}...")
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                raw_mapping = json.load(f)
                # Normalize keys in existing mapping
                existing_mapping = {
                    normalize_linkedin_url(url): data
                    for url, data in raw_mapping.items()
                    if normalize_linkedin_url(url)
                }
            print(f"✅ Loaded {len(existing_mapping):,} existing entries")
        except Exception as e:
            print(f"⚠️  Could not load existing mapping: {e}")
            existing_mapping = {}
    else:
        print(f"\n📄 No existing mapping file found - starting fresh")

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

    # Filter out profiles that are already in mapping or filesystem
    profiles_to_process = []
    skipped_count = 0

    print(f"\n🔍 Checking which profiles need downloading...")
    for profile in profiles:
        linkedin_url = profile.get('linkedinUrl')
        if not linkedin_url:
            continue

        normalized_url = normalize_linkedin_url(linkedin_url)

        # Check mapping first
        if normalized_url in existing_mapping:
            existing_entry = existing_mapping[normalized_url]
            if existing_entry.get('status') == 'success' and existing_entry.get('local_path'):
                if is_valid_image(existing_entry['local_path']):
                    skipped_count += 1
                    continue

        # Check filesystem
        username = sanitize_linkedin_url(linkedin_url)
        output_path = os.path.join(OUTPUT_DIR, f"{username}.jpg")
        if os.path.exists(output_path) and is_valid_image(output_path):
            skipped_count += 1
            continue

        profiles_to_process.append(profile)

    print(f"✅ Analysis complete:")
    print(f"   • Total profiles: {total_profiles:,}")
    print(f"   • Already downloaded (valid): {skipped_count:,}")
    print(f"   • Need to download: {len(profiles_to_process):,}")

    if len(profiles_to_process) == 0:
        print(f"\n✅ All profiles already have valid images! Nothing to download.")
        return

    # Ask user for confirmation and how many to process (or auto-download all)
    print(f"\n{'='*60}")
    print(f"READY TO DOWNLOAD")
    print(f"{'='*60}")
    print(f"📥 {len(profiles_to_process):,} profiles need images")
    print(f"⏱️  Estimated time: ~{len(profiles_to_process) * 0.2:.1f} seconds ({BATCH_SIZE} concurrent)")
    print(f"💾 Estimated storage: ~{len(profiles_to_process) * 15 / 1024:.1f} MB")

    if auto_mode:
        # Auto mode - download all without prompting
        profiles_to_download = profiles_to_process
        print(f"\n🤖 AUTO MODE: Downloading all {len(profiles_to_download):,} profiles")
    else:
        # Interactive mode - ask user
        while True:
            try:
                user_input = input(f"\nHow many profiles to download? (1-{len(profiles_to_process):,}, or 'all' or 'cancel'): ").strip().lower()

                if user_input == 'cancel':
                    print("❌ Download cancelled by user")
                    return
                elif user_input == 'all':
                    profiles_to_download = profiles_to_process
                    break
                else:
                    num_to_download = int(user_input)
                    if 1 <= num_to_download <= len(profiles_to_process):
                        profiles_to_download = profiles_to_process[:num_to_download]
                        remaining = len(profiles_to_process) - num_to_download
                        if remaining > 0:
                            print(f"📋 {remaining:,} profiles will remain for next run")
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(profiles_to_process):,}, 'all', or 'cancel'")
            except ValueError:
                print("Please enter a valid number, 'all', or 'cancel'")

    print(f"\n🚀 Starting download of {len(profiles_to_download):,} profile pictures...")

    # Statistics
    stats = {
        'total': len(profiles_to_download),
        'success': 0,
        'skipped_mapping': 0,
        'skipped_filesystem': 0,
        'no_image': 0,
        'failed': 0,
        'redownloaded': 0
    }

    mapping = {}

    # Process profiles with thread pool
    print(f"\n⬇️  Downloading profile pictures (batch size: {BATCH_SIZE})...")
    print(f"⏱️  Timeout: {TIMEOUT}s, Retries: {MAX_RETRIES}")
    print()

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Submit all tasks for selected profiles
        futures = {
            executor.submit(process_profile, profile, default_image_path, existing_mapping): profile
            for profile in profiles_to_download
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
            if completed % 100 == 0 or completed == len(profiles_to_download):
                print(f"📈 Progress: {completed}/{len(profiles_to_download)} ({completed/len(profiles_to_download)*100:.1f}%)")

    # Save mapping file (merge with existing)
    print(f"\n💾 Saving mapping file to {MAPPING_FILE}...")

    # Load existing mapping again to merge (in case it changed)
    final_mapping = {}
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                final_mapping = json.load(f)
        except Exception:
            pass

    # Merge new mappings into existing
    final_mapping.update(mapping)

    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_mapping, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved mapping with {len(final_mapping):,} total entries ({len(mapping):,} new)")

    # Display statistics
    print(f"\n📊 DOWNLOAD STATISTICS")
    print("=" * 60)
    print(f"Total profiles: {stats['total']:,}")
    print(f"✅ Successfully downloaded: {stats.get('success', 0):,}")
    print(f"⏩ Skipped (in mapping): {stats.get('skipped_mapping', 0):,}")
    print(f"⏩ Skipped (filesystem check): {stats.get('skipped_filesystem', 0):,}")
    print(f"🔄 Re-downloaded (invalid): {stats.get('redownloaded', 0):,}")
    print(f"❌ Failed downloads: {stats.get('failed', 0):,}")
    print(f"❌ No profile picture URL: {stats.get('no_image', 0):,}")
    print(f"\n💡 Total skipped: {stats.get('skipped_mapping', 0) + stats.get('skipped_filesystem', 0):,}")
    print(f"💡 Missing pictures will show HiUser icon in frontend")

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

    # Show remaining work if applicable
    if len(profiles_to_download) < len(profiles_to_process):
        remaining = len(profiles_to_process) - len(profiles_to_download)
        print(f"\n📋 REMAINING WORK:")
        print(f"   • {remaining:,} profiles still need images")
        print(f"   • Run the script again to continue downloading")

if __name__ == "__main__":
    main()
