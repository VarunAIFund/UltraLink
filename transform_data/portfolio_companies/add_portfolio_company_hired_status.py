#!/usr/bin/env python3
"""
Add Portfolio Company Hired Status to Structured Profiles

This script checks each profile's experiences for mentions of AI Fund portfolio companies
and DeepLearning.AI, and marks those candidates as hired by adding entries to their
lever_opportunities array with hired: true.

Usage:
    python add_portfolio_company_hired_status.py
"""

import json
import os
from typing import Dict, List, Any

# AI Fund portfolio companies and related companies to check for hired status
PORTFOLIO_COMPANIES = [
    "10Web.io",
    "Affineon Health",
    "Baseten",
    "Bearing",
    "Bhuma",
    "BizTrip AI",
    "BNTO",
    "Civio.ai",
    "Common Sense Privacy",
    "Credo AI",
    "Esteam",
    "Factored AI",
    "Factored",  # Also check without "AI"
    "Feenyx",
    "Freight Hero",
    "Gaia Dynamics",
    "Haven Safety",
    "IrisGo",
    "Jivi AI",
    "Kira",
    "LandingAI",
    "Meeno",
    "Octagon",
    "Olakai",
    "Pixi Platforms",
    "Podcastle",
    "Profitmind",
    "PuppyDog.io",
    "RapidFire AI",
    "RealAvatar",
    "Rypple",
    "Skyfire",
    "SpeechLab",
    "StrongSuit",
    "Sunrise AI",
    "ValidMind",
    "WhyLabs",
    "Woebot Health",
    "Workera",
    "Workhelix",
    "AI Fund",
    "DeepLearning.AI",
]

def normalize_name(name: str) -> str:
    """Normalize name for case-insensitive matching"""
    return name.strip().lower() if name else ""

def load_profiles(profiles_file: str) -> List[Dict[str, Any]]:
    """Load structured profiles from JSON file"""
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        print(f"✅ Loaded {len(profiles)} profiles")
        return profiles
    except FileNotFoundError:
        print(f"❌ Profiles file not found: {profiles_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return []

def save_profiles(profiles: List[Dict[str, Any]], output_file: str) -> bool:
    """Save updated profiles to JSON file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(profiles)} profiles")
        return True
    except Exception as e:
        print(f"❌ Error saving: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 Add Portfolio Company Hired Status")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_file = os.path.join(script_dir, '..', 'structured_profiles_test.json')
    
    if not os.path.exists(profiles_file):
        print(f"❌ Profiles file not found: {profiles_file}")
        return
    
    # Normalize portfolio company names for matching
    normalized_portfolio = {normalize_name(comp): comp for comp in PORTFOLIO_COMPANIES}
    
    # Load profiles
    profiles = load_profiles(profiles_file)
    if not profiles:
        return
    
    # Check each profile
    stats = {
        'total': len(profiles),
        'marked_hired': 0,
        'already_hired': 0
    }
    
    for profile in profiles:
        experiences = profile.get('experiences', [])
        if not experiences:
            continue
        
        # Check if any experience org matches a portfolio company
        matched_company = None
        for exp in experiences:
            org = exp.get('org', '')
            normalized_org = normalize_name(org)
            if normalized_org in normalized_portfolio:
                matched_company = normalized_portfolio[normalized_org]
                break
        
        if matched_company:
            # Initialize lever_opportunities if needed
            if 'lever_opportunities' not in profile:
                profile['lever_opportunities'] = []
            
            # Check if already marked as hired (any entry with hired: true and no URL field)
            already_has_portfolio_hired = any(
                opp.get('hired') == True and 'url' not in opp
                for opp in profile['lever_opportunities']
            )
            
            if not already_has_portfolio_hired:
                # Add portfolio company entry with just hired: true (no URL field)
                profile['lever_opportunities'].append({
                    'hired': True
                })
                stats['marked_hired'] += 1
            else:
                stats['already_hired'] += 1
    
    # Print statistics
    print(f"\n📊 Results:")
    print(f"   Total profiles: {stats['total']:,}")
    print(f"   Newly marked as hired: {stats['marked_hired']:,}")
    print(f"   Already marked: {stats['already_hired']:,}")
    print("="*60)
    
    # Save updated profiles
    if save_profiles(profiles, profiles_file):
        print("✅ Complete! Profiles updated with portfolio company hired status.")

if __name__ == "__main__":
    main()
