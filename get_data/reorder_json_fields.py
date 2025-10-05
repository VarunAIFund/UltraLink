#!/usr/bin/env python3
"""
Reorder JSON Fields

Reorders LinkedIn profile JSON structure to place 'connected_to' field after 'followers'.
Maintains consistent field ordering across all profiles for better readability and processing.
"""

import json
import os
from collections import OrderedDict

def reorder_profile_fields(profile):
    """Reorder fields in a single profile to put connected_to after followers"""
    
    # Create new ordered dictionary
    ordered_profile = OrderedDict()
    
    # Add fields in desired order
    for key, value in profile.items():
        ordered_profile[key] = value
        
        # If we just added followers, add connected_to next (if it exists)
        if key == 'followers' and 'connected_to' in profile:
            ordered_profile['connected_to'] = profile['connected_to']
    
    # Remove connected_to from its original position if it was added after followers
    if 'followers' in profile and 'connected_to' in profile:
        # Create final ordered dict without duplicate connected_to
        final_profile = OrderedDict()
        connected_to_added = False
        
        for key, value in ordered_profile.items():
            if key == 'connected_to' and connected_to_added:
                continue  # Skip duplicate
            elif key == 'followers':
                final_profile[key] = value
                if 'connected_to' in profile:
                    final_profile['connected_to'] = profile['connected_to']
                    connected_to_added = True
            elif key == 'connected_to' and not connected_to_added:
                final_profile[key] = value
                connected_to_added = True
            else:
                final_profile[key] = value
        
        return dict(final_profile)
    
    return dict(ordered_profile)

def reorder_json_fields(input_file="results/linda_connections.json"):
    """Reorder fields in all profiles"""
    
    print(f"🔄 Reordering fields in: {input_file}")
    
    # Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total profiles to process: {len(profiles)}")
    
    # Process each profile
    reordered_profiles = []
    profiles_with_followers = 0
    profiles_with_connected_to = 0
    profiles_reordered = 0
    
    for i, profile in enumerate(profiles):
        if 'followers' in profile:
            profiles_with_followers += 1
        
        if 'connected_to' in profile:
            profiles_with_connected_to += 1
        
        # Reorder fields
        reordered_profile = reorder_profile_fields(profile)
        reordered_profiles.append(reordered_profile)
        
        # Check if reordering was applied
        if 'followers' in profile and 'connected_to' in profile:
            profiles_reordered += 1
    
    print(f"✅ Profiles with 'followers' field: {profiles_with_followers}")
    print(f"✅ Profiles with 'connected_to' field: {profiles_with_connected_to}")
    print(f"🔄 Profiles reordered: {profiles_reordered}")
    
    # Create backup
    backup_file = input_file + '.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    print(f"📄 Created backup: {backup_file}")
    
    # Save reordered data
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(reordered_profiles, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Saved reordered profiles to: {input_file}")
    
    # Show example of reordered structure
    if reordered_profiles:
        print(f"\n🔍 Example of reordered profile structure:")
        example = reordered_profiles[0]
        
        # Show fields around followers and connected_to
        fields = list(example.keys())
        if 'followers' in fields:
            followers_idx = fields.index('followers')
            start_idx = max(0, followers_idx - 2)
            end_idx = min(len(fields), followers_idx + 4)
            
            print(f"Field order around 'followers':")
            for i in range(start_idx, end_idx):
                field = fields[i]
                marker = "→ " if field in ['followers', 'connected_to'] else "  "
                print(f"{marker}{field}: {type(example[field]).__name__}")
    
    print(f"\n📈 Summary:")
    print(f"  - Processed {len(profiles)} profiles")
    print(f"  - Reordered {profiles_reordered} profiles")
    print(f"  - 'connected_to' now appears after 'followers' in all applicable profiles")

def main():
    """Main function"""
    reorder_json_fields()

if __name__ == "__main__":
    main()