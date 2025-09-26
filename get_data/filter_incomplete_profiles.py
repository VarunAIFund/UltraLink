#!/usr/bin/env python3
"""
Filter Incomplete Profiles

Separates profiles with null fullName into a different JSON file
"""

import json
import os

def filter_profiles(input_file="results/linda_connections.json"):
    """Filter profiles based on fullName field"""
    
    # Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total profiles loaded: {len(all_profiles)}")
    
    # Separate profiles
    valid_profiles = []
    incomplete_profiles = []
    
    for profile in all_profiles:
        full_name = profile.get('fullName')
        
        # Check if fullName is null, empty string, or missing
        if full_name is None or full_name == "" or full_name == "null":
            incomplete_profiles.append(profile)
        else:
            valid_profiles.append(profile)
    
    print(f"✅ Valid profiles (with fullName): {len(valid_profiles)}")
    print(f"❌ Incomplete profiles (null fullName): {len(incomplete_profiles)}")
    
    # Save valid profiles back to original file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(valid_profiles, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Updated {input_file} with valid profiles only")
    
    # Save incomplete profiles to separate file
    if incomplete_profiles:
        incomplete_file = input_file.replace('.json', '_incomplete.json')
        with open(incomplete_file, 'w', encoding='utf-8') as f:
            json.dump(incomplete_profiles, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved incomplete profiles to: {incomplete_file}")
        
        # Show example of incomplete profile
        print("\n🔍 Example incomplete profile:")
        example = incomplete_profiles[0]
        print(f"LinkedIn URL: {example.get('linkedinUrl', 'N/A')}")
        print(f"Full Name: {example.get('fullName')}")
        print(f"Headline: {example.get('headline', 'N/A')}")
    else:
        print("✅ No incomplete profiles found!")
    
    print(f"\n📈 Summary:")
    print(f"  - Kept {len(valid_profiles)} complete profiles")
    print(f"  - Moved {len(incomplete_profiles)} incomplete profiles") 
    print(f"  - Success rate: {(len(valid_profiles) / len(all_profiles)) * 100:.1f}%")

def main():
    """Main function"""
    filter_profiles()

if __name__ == "__main__":
    main()