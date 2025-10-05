#!/usr/bin/env python3
"""
Add Connection Source

Adds a 'connected_to' array field to each LinkedIn profile indicating the connection source.
Tracks who each person is connected to for relationship mapping and network analysis.
"""

import json
import os

def add_connection_source(input_file="results/linda_connections.json", connection_name="linda"):
    """Add connected_to field to all profiles"""
    
    # Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Total profiles loaded: {len(profiles)}")
    
    # Add connected_to field to each profile
    updated_count = 0
    for profile in profiles:
        # Add connected_to as an array
        profile['connected_to'] = [connection_name]
        updated_count += 1
    
    # Save updated data back to file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated {updated_count} profiles with connected_to field")
    print(f"📄 Saved updated data to: {input_file}")
    
    # Show example of updated profile
    if profiles:
        print("\n🔍 Example updated profile structure:")
        example = profiles[0]
        print(f"LinkedIn URL: {example.get('linkedinUrl', 'N/A')}")
        print(f"Full Name: {example.get('fullName', 'N/A')}")
        print(f"Connected To: {example.get('connected_to', [])}")

def main():
    """Main function"""
    add_connection_source()

if __name__ == "__main__":
    main()