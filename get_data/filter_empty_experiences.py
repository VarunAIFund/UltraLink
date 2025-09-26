#!/usr/bin/env python3
"""
Filter Profiles with Empty Experiences

Separates profiles with null fullName AND empty experiences into different JSON files
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
    no_experiences_profiles = []
    incomplete_profiles = []
    
    for profile in all_profiles:
        full_name = profile.get('fullName')
        experiences = profile.get('experiences', [])
        
        # Check if fullName is null, empty string, or missing
        if full_name is None or full_name == "" or full_name == "null":
            incomplete_profiles.append(profile)
        # Check if experiences array is empty
        elif not experiences or len(experiences) == 0:
            no_experiences_profiles.append(profile)
        else:
            complete_profiles.append(profile)
    
    print(f"✅ Complete profiles (with fullName & experiences): {len(complete_profiles)}")
    print(f"🔍 Profiles with empty experiences: {len(no_experiences_profiles)}")
    print(f"❌ Incomplete profiles (null fullName): {len(incomplete_profiles)}")
    
    # Save complete profiles back to original file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(complete_profiles, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Updated {input_file} with complete profiles only")
    
    # Save profiles with no experiences to separate file
    if no_experiences_profiles:
        no_exp_file = input_file.replace('.json', '_no_experiences.json')
        with open(no_exp_file, 'w', encoding='utf-8') as f:
            json.dump(no_experiences_profiles, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved profiles with empty experiences to: {no_exp_file}")
        
        # Show example of profile with no experiences
        print("\n🔍 Example profile with empty experiences:")
        example = no_experiences_profiles[0]
        print(f"LinkedIn URL: {example.get('linkedinUrl', 'N/A')}")
        print(f"Full Name: {example.get('fullName', 'N/A')}")
        print(f"Headline: {example.get('headline', 'N/A')}")
        print(f"Experiences: {example.get('experiences', [])}")
    else:
        print("✅ No profiles with empty experiences found!")
    
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
    print(f"  - Kept {len(complete_profiles)} complete profiles")
    print(f"  - Moved {len(no_experiences_profiles)} profiles with empty experiences")
    print(f"  - Moved {len(incomplete_profiles)} incomplete profiles") 
    print(f"  - Complete success rate: {(len(complete_profiles) / len(all_profiles)) * 100:.1f}%")
    print(f"  - Profiles with data issues: {((len(no_experiences_profiles) + len(incomplete_profiles)) / len(all_profiles)) * 100:.1f}%")

def main():
    """Main function"""
    filter_profiles()

if __name__ == "__main__":
    main()