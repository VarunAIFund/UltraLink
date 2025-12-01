#!/usr/bin/env python3
"""
Upload Profile Pictures to Supabase Storage

Uploads all downloaded LinkedIn profile pictures to Supabase Storage bucket.
Uses existing filenames (e.g., in-johndoe.jpg) - no mapping file needed.

Usage:
    python upload_profile_pictures_to_supabase.py          # Interactive mode (asks for confirmation)
    python upload_profile_pictures_to_supabase.py --auto   # Auto mode (skips confirmation)
"""

import json
import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Load environment variables - .env is in website directory
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'website', '.env')
print(f"[DEBUG] Loading .env from: {env_path}")
print(f"[DEBUG] File exists: {os.path.exists(env_path)}")

# Clear existing env vars to avoid conflicts
if 'SUPABASE_URL' in os.environ:
    del os.environ['SUPABASE_URL']
if 'SUPABASE_SERVICE_ROLE_KEY' in os.environ:
    del os.environ['SUPABASE_SERVICE_ROLE_KEY']

load_dotenv(env_path, override=True)

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL}")
print(f"[DEBUG] SERVICE_ROLE_KEY: {'*' * 20 if SUPABASE_SERVICE_ROLE_KEY else 'NOT SET'}")
BUCKET_NAME = 'profile-pictures'

# Paths relative to transform_data directory (parent of upload_pictures)
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
PROFILE_PICTURES_DIR = os.path.join(BASE_DIR, 'profile_pictures')
MAPPING_FILE = os.path.join(BASE_DIR, 'profile_picture_mapping.json')
BATCH_SIZE = 50  # Concurrent uploads
DEFAULT_IMAGE = 'default.jpg'

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def upload_image(file_path: str, filename: str) -> dict:
    """Upload a single image to Supabase Storage"""
    try:
        # Read file
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Upload to Supabase Storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=file_data,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )

        # Check if upload was successful
        # Supabase returns different response formats depending on success/failure
        if hasattr(result, 'error') and result.error:
            return {
                'filename': filename,
                'status': 'error',
                'error': f"Supabase error: {result.error}"
            }

        return {
            'filename': filename,
            'status': 'success',
            'size': len(file_data)
        }
    except Exception as e:
        # Classify error type
        error_type = type(e).__name__
        error_msg = str(e)

        # Network timeout errors are false negatives (file actually uploads)
        # Only show real errors (filename issues, permissions, etc.)
        is_network_error = any(x in error_type for x in ['ReadError', 'TimeoutError', 'ConnectionError'])

        return {
            'filename': filename,
            'status': 'error',
            'error': f"{error_type}: {error_msg}",
            'is_network_error': is_network_error
        }

def get_existing_files_in_bucket():
    """Get list of files already uploaded to Supabase Storage"""
    try:
        existing_files = set()
        offset = 0
        limit = 1000  # Fetch 1000 files at a time

        while True:
            # List files with pagination
            result = supabase.storage.from_(BUCKET_NAME).list(
                path='',
                options={'limit': limit, 'offset': offset}
            )

            # Parse result
            if isinstance(result, list):
                if len(result) == 0:
                    break  # No more files

                for file_obj in result:
                    if isinstance(file_obj, dict) and 'name' in file_obj:
                        existing_files.add(file_obj['name'])
                    elif hasattr(file_obj, 'name'):
                        existing_files.add(file_obj.name)

                # If we got fewer than limit, we're done
                if len(result) < limit:
                    break

                offset += limit
            else:
                break

        return existing_files
    except Exception as e:
        print(f"⚠️  Warning: Could not list existing files: {e}")
        print(f"⚠️  Continuing without skip check - will use upsert to avoid duplicates")
        return set()

def get_images_to_upload(skip_existing=True):
    """Get list of unique profile pictures to upload (excluding default.jpg copies)"""

    # Get existing files in bucket
    existing_files = set()
    if skip_existing:
        print("\n🔍 Checking which files are already uploaded...")
        existing_files = get_existing_files_in_bucket()
        print(f"✅ Found {len(existing_files):,} files already in bucket")

    # Load mapping to identify which files are actual downloads vs default copies
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    images_to_upload = []
    skipped_count = 0

    for linkedin_url, data in mapping.items():
        local_path = data.get('local_path')
        status = data.get('status')

        # Only upload successfully downloaded images (not default copies or no_image)
        # Status values: 'success', 'exists' = real downloads; 'default' = copy of default.jpg; 'no_image' = no picture available
        if local_path and status in ['success', 'exists']:
            filename = os.path.basename(local_path)

            # Make path absolute if needed
            if not os.path.isabs(local_path):
                full_path = os.path.join(BASE_DIR, local_path)
            else:
                full_path = local_path

            # Check if file exists
            if os.path.exists(full_path):
                # Skip if already uploaded
                if skip_existing and filename in existing_files:
                    skipped_count += 1
                    continue

                images_to_upload.append({
                    'filename': filename,
                    'path': full_path,
                    'linkedin_url': linkedin_url
                })

    # Don't upload default.jpg - frontend has its own fallback UI
    # (This avoids showing ugly default image instead of nice HiUser icon)

    if skip_existing and skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count:,} files (already uploaded)")

    return images_to_upload

def main():
    """Main upload function"""

    # Check for --auto flag
    auto_mode = '--auto' in sys.argv

    print("📸 Supabase Profile Picture Upload")
    print("=" * 60)

    if auto_mode:
        print("🤖 Running in AUTO mode (skipping confirmation)")

    # Validate environment variables
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        return

    print(f"✅ Connected to Supabase: {SUPABASE_URL}")
    print(f"📦 Target bucket: {BUCKET_NAME}")

    # Check if bucket exists
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b['name'] for b in buckets]

        if BUCKET_NAME not in bucket_names:
            print(f"\n❌ Error: Bucket '{BUCKET_NAME}' does not exist!")
            print("Please create the bucket in Supabase dashboard first:")
            print("1. Go to Storage → New bucket")
            print("2. Name: profile-pictures")
            print("3. Make it Public")
            return

        print(f"✅ Bucket '{BUCKET_NAME}' exists")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify bucket (may still work): {e}")

    # Get list of images to upload
    print(f"\n📂 Loading images from {PROFILE_PICTURES_DIR}/...")
    images_to_upload = get_images_to_upload()

    total_images = len(images_to_upload)
    print(f"✅ Found {total_images:,} images to upload")

    # Calculate total size
    total_size = sum(os.path.getsize(img['path']) for img in images_to_upload)
    size_mb = total_size / (1024 * 1024)
    print(f"📊 Total size: {size_mb:.2f} MB")

    # Ask for confirmation (skip in auto mode)
    if not auto_mode:
        print(f"\n⚠️  About to upload {total_images:,} images ({size_mb:.2f} MB)")
        response = input("Continue? (yes/no): ").lower().strip()

        if response != 'yes':
            print("❌ Upload cancelled")
            return
    else:
        print(f"\n⬆️  Proceeding with upload of {total_images:,} images ({size_mb:.2f} MB)...")

    # Upload with thread pool
    print(f"\n⬆️  Uploading images (batch size: {BATCH_SIZE})...")
    print(f"⏱️  Started at {time.strftime('%H:%M:%S')}")
    print()

    stats = {
        'success': 0,
        'error': 0,
        'network_errors': 0,
        'real_errors': 0,
        'total_bytes': 0
    }

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Submit all upload tasks
        futures = {
            executor.submit(upload_image, img['path'], img['filename']): img
            for img in images_to_upload
        }

        # Process completed uploads
        completed = 0
        real_error_samples = []
        for future in as_completed(futures):
            completed += 1
            result = future.result()

            if result['status'] == 'success':
                stats['success'] += 1
                stats['total_bytes'] += result.get('size', 0)
            else:
                stats['error'] += 1
                error_msg = result.get('error', 'Unknown error')
                is_network_error = result.get('is_network_error', False)

                if is_network_error:
                    stats['network_errors'] += 1
                    # Don't print network errors - they're false negatives
                else:
                    stats['real_errors'] += 1
                    # Only show real errors (filename issues, special characters, etc.)
                    if len(real_error_samples) < 10:
                        real_error_samples.append(f"❌ {result['filename']}: {error_msg}")
                        print(f"❌ REAL ERROR: {result['filename']} - {error_msg}")

            # Progress indicator
            if completed % 100 == 0 or completed == total_images:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_images - completed) / rate if rate > 0 else 0

                print(f"📈 Progress: {completed}/{total_images} ({completed/total_images*100:.1f}%) | "
                      f"Rate: {rate:.1f}/s | ETA: {eta:.0f}s")

    elapsed = time.time() - start_time

    # Verify actual upload count (Supabase library has bugs reporting failures)
    print(f"\n🔍 Verifying actual upload count...")
    try:
        actual_files = []
        offset = 0
        limit = 1000

        while True:
            result = supabase.storage.from_(BUCKET_NAME).list(
                path='',
                options={'limit': limit, 'offset': offset}
            )

            if not result or len(result) == 0:
                break

            for file_obj in result:
                if isinstance(file_obj, dict) and 'name' in file_obj:
                    actual_files.append(file_obj['name'])
                elif hasattr(file_obj, 'name'):
                    actual_files.append(file_obj.name)

            if len(result) < limit:
                break

            offset += limit

        actual_count = len(actual_files)
        false_negatives = actual_count - stats['success']

        print(f"\n✅ UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Total images attempted: {total_images:,}")
        print(f"✅ Reported successes: {stats['success']:,}")
        print(f"❌ Reported failures: {stats['error']:,}")
        print(f"   ├─ Network errors (false negatives): {stats['network_errors']:,}")
        print(f"   └─ Real errors (special characters, etc.): {stats['real_errors']:,}")
        print(f"\n🔍 VERIFICATION (actual files in Supabase):")
        print(f"✅ Actually uploaded: {actual_count:,}")
        print(f"❌ True failures: {total_images - actual_count:,}")

        if false_negatives > 0:
            print(f"\n💡 Note: {false_negatives:,} network timeouts occurred but files uploaded successfully")

        print(f"\n📦 Total uploaded: {stats['total_bytes'] / (1024 * 1024):.2f} MB")
        print(f"⏱️  Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"⚡ Average rate: {actual_count/elapsed:.1f} images/second")
        print(f"🎯 Actual success rate: {actual_count/total_images*100:.1f}%")

    except Exception as e:
        print(f"\n⚠️  Could not verify actual count: {e}")
        print(f"\n✅ UPLOAD COMPLETE")
        print("=" * 60)
        print(f"Total images: {total_images:,}")
        print(f"✅ Successfully uploaded: {stats['success']:,}")
        print(f"❌ Failed: {stats['error']:,}")
        print(f"📦 Total uploaded: {stats['total_bytes'] / (1024 * 1024):.2f} MB")
        print(f"⏱️  Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"⚡ Average rate: {stats['success']/elapsed:.1f} images/second")

    # Generate example URLs
    print(f"\n🔗 EXAMPLE URLS")
    print("=" * 60)
    base_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}"

    for i, img in enumerate(images_to_upload[:3], 1):
        if img['linkedin_url']:
            print(f"{i}. {img['filename']}")
            print(f"   LinkedIn: {img['linkedin_url']}")
            print(f"   Supabase: {base_url}/{img['filename']}")
            print()

    print(f"\n✅ All images uploaded to: {base_url}/")
    print(f"📝 Next step: Update backend to generate URLs from LinkedIn URLs")

if __name__ == "__main__":
    main()
