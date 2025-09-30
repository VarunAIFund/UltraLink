#!/usr/bin/env python3
"""
Filter Profiles - Combined

Removes profiles with null fullName OR empty experiences from main file
Saves all filtered profiles to one combined file
"""

import json
import os

def filter_profiles(input_file="results/linda_connections.json"):
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

def main():
    """Main function"""
    filter_profiles()

if __name__ == "__main__":
    main()