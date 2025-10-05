#!/usr/bin/env python3
"""
Filter Profiles - Combined

Removes incomplete LinkedIn profiles with null fullName OR empty experiences from dataset.
Creates backups and saves filtered profiles to separate files for quality assurance.
"""

import json
import os

def filter_profiles(input_file="results/connections.json"):
    """Filter profiles based on fullName and experiences fields"""
    
    # Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total profiles loaded: {len(all_profiles)}")
    
    # Separate profiles
    complete_profiles = []
    filtered_profiles = []
    
    # Count reasons for filtering
    null_fullname_count = 0
    empty_experiences_count = 0
    
    for profile in all_profiles:
        full_name = profile.get('fullName')
        experiences = profile.get('experiences', [])
        
        # Check if fullName is null, empty string, or missing
        has_null_fullname = full_name is None or full_name == "" or full_name == "null"
        
        # Check if experiences array is empty
        has_empty_experiences = not experiences or len(experiences) == 0
        
        if has_null_fullname or has_empty_experiences:
            # Add reason for filtering
            reasons = []
            if has_null_fullname:
                reasons.append("null_fullname")
                null_fullname_count += 1
            if has_empty_experiences:
                reasons.append("empty_experiences")
                empty_experiences_count += 1
            
            profile['filter_reason'] = reasons
            filtered_profiles.append(profile)
        else:
            complete_profiles.append(profile)
    
    print(f"✅ Complete profiles (kept): {len(complete_profiles)}")
    print(f"❌ Filtered profiles (removed): {len(filtered_profiles)}")
    print(f"   - Null fullName: {null_fullname_count}")
    print(f"   - Empty experiences: {empty_experiences_count}")
    
    # Save complete profiles back to original file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(complete_profiles, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Updated {input_file} with complete profiles only")
    
    # Save all filtered profiles to one combined file
    if filtered_profiles:
        filtered_file = input_file.replace('.json', '_filtered_out.json')
        with open(filtered_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_profiles, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved all filtered profiles to: {filtered_file}")
        
        # Show examples of filtered profiles
        print("\n🔍 Examples of filtered profiles:")
        
        # Example with null fullName
        null_example = next((p for p in filtered_profiles if "null_fullname" in p.get('filter_reason', [])), None)
        if null_example:
            print("  Null fullName example:")
            print(f"    LinkedIn URL: {null_example.get('linkedinUrl', 'N/A')}")
            print(f"    Full Name: {null_example.get('fullName')}")
            print(f"    Filter Reason: {null_example.get('filter_reason', [])}")
        
        # Example with empty experiences
        empty_exp_example = next((p for p in filtered_profiles if "empty_experiences" in p.get('filter_reason', [])), None)
        if empty_exp_example:
            print("  Empty experiences example:")
            print(f"    LinkedIn URL: {empty_exp_example.get('linkedinUrl', 'N/A')}")
            print(f"    Full Name: {empty_exp_example.get('fullName', 'N/A')}")
            print(f"    Experiences: {empty_exp_example.get('experiences', [])}")
            print(f"    Filter Reason: {empty_exp_example.get('filter_reason', [])}")
    else:
        print("✅ No profiles needed filtering!")
    
    print(f"\n📈 Summary:")
    print(f"  - Kept {len(complete_profiles)} complete profiles in main file")
    print(f"  - Moved {len(filtered_profiles)} incomplete profiles to filtered file")
    print(f"  - Success rate: {(len(complete_profiles) / len(all_profiles)) * 100:.1f}%")

def preview_filter(input_file="results/connections.json"):
    """Preview how many profiles would be filtered"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return 0, 0
    
    # Count profiles that would be filtered
    null_name_count = 0
    empty_exp_count = 0
    
    for profile in all_profiles:
        full_name = profile.get('fullName')
        experiences = profile.get('experiences', [])
        
        if not full_name or full_name.strip() == "":
            null_name_count += 1
        elif not experiences or len(experiences) == 0:
            empty_exp_count += 1
    
    total_to_filter = null_name_count + empty_exp_count
    total_to_keep = len(all_profiles) - total_to_filter
    
    return len(all_profiles), total_to_filter, null_name_count, empty_exp_count, total_to_keep

def main():
    """Main function"""
    print("🔗 LinkedIn Profile Filter")
    print("=" * 50)
    
    # Preview the filtering
    total_profiles, profiles_to_filter, null_names, empty_experiences, profiles_to_keep = preview_filter()
    
    if total_profiles == 0:
        return
    
    print(f"📊 Preview:")
    print(f"  Total profiles: {total_profiles}")
    print(f"  Complete profiles (keep): {profiles_to_keep}")
    print(f"  Incomplete profiles (filter): {profiles_to_filter}")
    print(f"    - Profiles with null/empty fullName: {null_names}")
    print(f"    - Profiles with empty experiences: {empty_experiences}")
    print(f"  Success rate: {(profiles_to_keep / total_profiles) * 100:.1f}%")
    
    # Ask for confirmation
    confirmation = input(f"\nProceed to filter out {profiles_to_filter} incomplete profiles? (y/n): ").strip().lower()
    
    if confirmation in ['y', 'yes']:
        filter_profiles()
    else:
        print("❌ Operation cancelled")

if __name__ == "__main__":
    main()