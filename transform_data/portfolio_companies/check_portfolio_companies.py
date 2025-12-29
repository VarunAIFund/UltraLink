#!/usr/bin/env python3
"""
Sanity check: See if there's at least one person for each portfolio company
in the structured profiles file.
"""

import json
import os
from collections import defaultdict

# Portfolio companies to check
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
    "Factored",
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

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_file = os.path.join(script_dir, '..', 'structured_profiles_test.json')
    
    print("🔍 Checking portfolio companies in structured profiles...")
    print("="*60)
    
    # Normalize portfolio company names for matching
    normalized_portfolio = {normalize_name(comp): comp for comp in PORTFOLIO_COMPANIES}
    
    # Track matches
    company_matches = defaultdict(list)  # company -> list of profile names
    
    # Load and check profiles
    print(f"\n📂 Loading profiles from {profiles_file}...")
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        print(f"✅ Loaded {len(profiles)} profiles\n")
    except Exception as e:
        print(f"❌ Error loading profiles: {e}")
        return
    
    # Check each profile
    for profile in profiles:
        name = profile.get('name', 'Unknown')
        experiences = profile.get('experiences', [])
        
        if not experiences:
            continue
        
        for exp in experiences:
            org = exp.get('org', '')
            if not org:
                continue
            
            normalized_org = normalize_name(org)
            if normalized_org in normalized_portfolio:
                company = normalized_portfolio[normalized_org]
                company_matches[company].append(name)
    
    # Print results
    print("📊 Results:\n")
    
    found_companies = []
    missing_companies = []
    
    for company in PORTFOLIO_COMPANIES:
        # Skip "Factored" if we're checking both "Factored AI" and "Factored"
        # (we'll handle "Factored AI" separately)
        if company == "Factored":
            # Check if "Factored AI" was found instead
            if "Factored AI" in company_matches:
                continue
        
        matches = company_matches.get(company, [])
        if matches:
            # Remove duplicates (same person might have multiple experiences)
            unique_matches = list(set(matches))
            found_companies.append(company)
            print(f"✅ {company}: {len(unique_matches)} person(s)")
            if len(unique_matches) <= 5:
                for person in unique_matches:
                    print(f"   - {person}")
            else:
                for person in unique_matches[:3]:
                    print(f"   - {person}")
                print(f"   ... and {len(unique_matches) - 3} more")
        else:
            missing_companies.append(company)
            print(f"❌ {company}: No matches found")
    
    # Summary
    print("\n" + "="*60)
    print(f"📈 Summary:")
    print(f"   Companies found: {len(found_companies)}/{len(PORTFOLIO_COMPANIES)}")
    print(f"   Companies missing: {len(missing_companies)}/{len(PORTFOLIO_COMPANIES)}")
    
    if missing_companies:
        print(f"\n⚠️  Companies with no matches:")
        for company in missing_companies:
            if company != "Factored":  # Skip since we check "Factored AI"
                print(f"   - {company}")

if __name__ == "__main__":
    main()

