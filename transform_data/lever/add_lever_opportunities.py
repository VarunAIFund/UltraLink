#!/usr/bin/env python3
"""
Add Lever Opportunities to Structured Profiles

This script reads linkedin_mapping_with_hired_status.json and adds a lever_opportunities field
to each profile in structured_profiles.json based on LinkedIn URL matching.
The field contains objects with {url, hired} format.

Usage:
    python add_lever_opportunities.py
"""

import json
import os
from typing import Dict, List, Any
from urllib.parse import urlparse, urlunparse

def normalize_linkedin_url(url: str) -> str:
    """
    Normalize LinkedIn URL to handle variations:
    - Add/remove www
    - Remove trailing slash
    - Ensure https protocol

    Examples:
        https://www.linkedin.com/in/john-doe/ -> https://linkedin.com/in/john-doe
        linkedin.com/in/john-doe -> https://linkedin.com/in/john-doe
        https://linkedin.com/in/john-doe/ -> https://linkedin.com/in/john-doe
    """
    if not url:
        return ""

    # Add https if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Parse URL
    parsed = urlparse(url)

    # Remove www from netloc
    netloc = parsed.netloc.replace('www.', '')

    # Remove trailing slash from path
    path = parsed.path.rstrip('/')

    # Reconstruct without www and trailing slash
    normalized = urlunparse((
        'https',  # Always use https
        netloc,
        path,
        '',  # params
        '',  # query
        ''   # fragment
    ))

    return normalized

def load_linkedin_mapping(mapping_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load LinkedIn to Lever URL mapping with hired status
    Returns: Dict mapping normalized LinkedIn URL -> List of {url, hired} objects
    """
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            raw_mapping = json.load(f)

        # Normalize all LinkedIn URLs in the mapping
        normalized_mapping = {}
        for linkedin_url, lever_opportunities in raw_mapping.items():
            normalized_url = normalize_linkedin_url(linkedin_url)
            normalized_mapping[normalized_url] = lever_opportunities

        print(f"✅ Loaded {len(normalized_mapping)} LinkedIn URLs from mapping file")
        return normalized_mapping

    except FileNotFoundError:
        print(f"❌ Mapping file not found: {mapping_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing mapping JSON: {e}")
        return {}

def load_structured_profiles(profiles_file: str) -> List[Dict[str, Any]]:
    """
    Load structured profiles from JSON file
    """
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        print(f"✅ Loaded {len(profiles)} profiles from {profiles_file}")
        return profiles

    except FileNotFoundError:
        print(f"❌ Profiles file not found: {profiles_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing profiles JSON: {e}")
        return []

def add_lever_opportunities(
    profiles: List[Dict[str, Any]],
    mapping: Dict[str, List[Dict[str, Any]]]
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Add lever_opportunities field to each profile based on LinkedIn URL
    Format: [{url: str, hired: bool}, ...]

    Returns:
        - Updated profiles list
        - Statistics dict with match counts
    """
    stats = {
        'total_profiles': len(profiles),
        'profiles_with_lever': 0,
        'profiles_without_lever': 0,
        'missing_linkedin_url': 0,
        'total_lever_urls': 0,
        'total_hired': 0
    }

    for profile in profiles:
        linkedin_url = profile.get('linkedinUrl')

        if not linkedin_url:
            profile['lever_opportunities'] = []
            stats['missing_linkedin_url'] += 1
            continue

        # Normalize the LinkedIn URL for lookup
        normalized_url = normalize_linkedin_url(linkedin_url)

        # Lookup Lever opportunities (now list of {url, hired} objects)
        lever_opportunities = mapping.get(normalized_url, [])
        profile['lever_opportunities'] = lever_opportunities

        if lever_opportunities:
            stats['profiles_with_lever'] += 1
            stats['total_lever_urls'] += len(lever_opportunities)
            # Count hired opportunities
            stats['total_hired'] += sum(1 for opp in lever_opportunities if opp.get('hired', False))
        else:
            stats['profiles_without_lever'] += 1

    return profiles, stats

def save_profiles(profiles: List[Dict[str, Any]], output_file: str) -> bool:
    """
    Save updated profiles to JSON file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(profiles)} profiles to {output_file}")
        return True

    except Exception as e:
        print(f"❌ Error saving profiles: {e}")
        return False

def print_statistics(stats: Dict[str, int]):
    """
    Print processing statistics
    """
    print(f"\n{'='*60}")
    print(f"📊 Processing Statistics:")
    print(f"   Total profiles: {stats['total_profiles']:,}")
    print(f"   Profiles with Lever opportunities: {stats['profiles_with_lever']:,}")
    print(f"   Profiles without Lever opportunities: {stats['profiles_without_lever']:,}")
    print(f"   Missing LinkedIn URL: {stats['missing_linkedin_url']:,}")
    print(f"   Total Lever URLs added: {stats['total_lever_urls']:,}")
    print(f"   Total hired: {stats['total_hired']:,}")

    if stats['total_profiles'] > 0:
        match_rate = (stats['profiles_with_lever'] / stats['total_profiles']) * 100
        print(f"   Match rate: {match_rate:.1f}%")

    if stats['total_lever_urls'] > 0:
        hired_rate = (stats['total_hired'] / stats['total_lever_urls']) * 100
        print(f"   Hired rate: {hired_rate:.1f}%")

    print(f"{'='*60}\n")

def main():
    """
    Main execution
    """
    print("🚀 Add Lever Opportunities to Structured Profiles")
    print("="*60)

    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(script_dir, 'linkedin_mapping_with_hired_status.json')
    profiles_file = os.path.join(script_dir, '..', 'structured_profiles_test.json')

    # Check if files exist
    if not os.path.exists(mapping_file):
        print(f"❌ Mapping file not found: {mapping_file}")
        return

    if not os.path.exists(profiles_file):
        print(f"❌ Profiles file not found: {profiles_file}")
        return

    # Load data
    print("\n1️⃣ Loading LinkedIn to Lever mapping...")
    mapping = load_linkedin_mapping(mapping_file)
    if not mapping:
        print("❌ No mapping data loaded. Exiting.")
        return

    print("\n2️⃣ Loading structured profiles...")
    profiles = load_structured_profiles(profiles_file)
    if not profiles:
        print("❌ No profiles loaded. Exiting.")
        return

    # Add Lever opportunities
    print("\n3️⃣ Adding Lever opportunities to profiles...")
    updated_profiles, stats = add_lever_opportunities(profiles, mapping)

    # Print statistics
    print_statistics(stats)

    # Save updated profiles
    print("4️⃣ Saving updated profiles...")
    success = save_profiles(updated_profiles, profiles_file)

    if success:
        print("✅ Process complete! Profiles updated with lever_opportunities field.")
    else:
        print("❌ Failed to save updated profiles.")

if __name__ == "__main__":
    main()
