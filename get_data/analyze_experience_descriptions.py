"""
Analyze experience descriptions in connections.json to determine if company scraping is needed
"""
import json
from collections import Counter

def analyze_descriptions(file_path="results/connections.json", min_length_threshold=200):
    """Analyze experience descriptions to see if company info scraping is needed

    Args:
        file_path: Path to connections.json
        min_length_threshold: Minimum character length to consider a description "substantial"
    """
    print(f"Loading {file_path}...")
    print(f"Using minimum description length threshold: {min_length_threshold} characters")

    with open(file_path, 'r') as f:
        profiles = json.load(f)

    total_profiles = len(profiles)
    total_experiences = 0
    experiences_with_description = 0
    experiences_with_company_desc = 0
    experiences_with_both = 0
    empty_descriptions = 0
    experiences_with_substantial_desc = 0  # NEW: descriptions >= threshold

    # Track description lengths
    description_lengths = []
    company_desc_lengths = []

    # Sample descriptions
    sample_descriptions = []
    sample_company_descriptions = []
    sample_short_descriptions = []

    # Track profiles
    profiles_with_any_description = 0
    profiles_with_any_company_desc = 0
    profiles_with_substantial_desc = 0  # NEW

    for profile in profiles:
        experiences = profile.get('experiences', [])

        if not experiences:
            continue

        has_any_desc = False
        has_any_company_desc = False
        has_any_substantial_desc = False

        for exp in experiences:
            total_experiences += 1

            # Check for experience description in subComponents
            has_exp_desc = False
            exp_desc_text = ""
            subComponents = exp.get('subComponents', [])
            for sub in subComponents:
                descriptions = sub.get('description', [])
                if descriptions:
                    for desc in descriptions:
                        if desc.get('type') == 'textComponent':
                            text = desc.get('text', '').strip()
                            if text:
                                has_exp_desc = True
                                has_any_desc = True
                                exp_desc_text = text
                                description_lengths.append(len(text))

                                if len(sample_descriptions) < 10:
                                    sample_descriptions.append({
                                        'name': profile.get('fullName'),
                                        'title': exp.get('title'),
                                        'company': exp.get('subtitle', '').split('·')[0].strip(),
                                        'description': text[:200] + ('...' if len(text) > 200 else ''),
                                        'length': len(text)
                                    })
                                break

            # Check if description is substantial (>= threshold)
            is_substantial = len(exp_desc_text) >= min_length_threshold
            if is_substantial:
                experiences_with_substantial_desc += 1
                has_any_substantial_desc = True
            elif has_exp_desc and len(sample_short_descriptions) < 5:
                # Collect short descriptions as examples
                sample_short_descriptions.append({
                    'name': profile.get('fullName'),
                    'title': exp.get('title'),
                    'company': exp.get('subtitle', '').split('·')[0].strip(),
                    'description': exp_desc_text,
                    'length': len(exp_desc_text)
                })

            # Check for company description
            company_desc = exp.get('companyDescription', '').strip()
            has_company_desc = False
            if company_desc:
                has_company_desc = True
                has_any_company_desc = True
                company_desc_lengths.append(len(company_desc))
                if len(sample_company_descriptions) < 10:
                    sample_company_descriptions.append({
                        'company': exp.get('subtitle', '').split('·')[0].strip(),
                        'description': company_desc[:200] + ('...' if len(company_desc) > 200 else ''),
                        'length': len(company_desc)
                    })

            # Count
            if has_exp_desc:
                experiences_with_description += 1
            if has_company_desc:
                experiences_with_company_desc += 1
            if has_exp_desc and has_company_desc:
                experiences_with_both += 1
            if not has_exp_desc and not has_company_desc:
                empty_descriptions += 1

        if has_any_desc:
            profiles_with_any_description += 1
        if has_any_company_desc:
            profiles_with_any_company_desc += 1
        if has_any_substantial_desc:
            profiles_with_substantial_desc += 1

    # Calculate averages
    avg_desc_length = sum(description_lengths) / len(description_lengths) if description_lengths else 0
    avg_company_desc_length = sum(company_desc_lengths) / len(company_desc_lengths) if company_desc_lengths else 0

    # Print statistics
    print(f"\n{'='*80}")
    print(f"PROFILE STATISTICS")
    print(f"{'='*80}")
    print(f"Total Profiles: {total_profiles:,}")
    print(f"Profiles with any experience description: {profiles_with_any_description:,} ({profiles_with_any_description/total_profiles*100:.1f}%)")
    print(f"Profiles with substantial descriptions (>={min_length_threshold} chars): {profiles_with_substantial_desc:,} ({profiles_with_substantial_desc/total_profiles*100:.1f}%)")
    print(f"Profiles with any company description: {profiles_with_any_company_desc:,} ({profiles_with_any_company_desc/total_profiles*100:.1f}%)")

    print(f"\n{'='*80}")
    print(f"EXPERIENCE STATISTICS")
    print(f"{'='*80}")
    print(f"Total Experiences: {total_experiences:,}")
    print(f"Experiences with description text: {experiences_with_description:,} ({experiences_with_description/total_experiences*100:.1f}%)")
    print(f"Experiences with SUBSTANTIAL descriptions (>={min_length_threshold} chars): {experiences_with_substantial_desc:,} ({experiences_with_substantial_desc/total_experiences*100:.1f}%)")
    print(f"Experiences with company description: {experiences_with_company_desc:,} ({experiences_with_company_desc/total_experiences*100:.1f}%)")
    print(f"Experiences with BOTH: {experiences_with_both:,} ({experiences_with_both/total_experiences*100:.1f}%)")
    print(f"Experiences with NEITHER (empty): {empty_descriptions:,} ({empty_descriptions/total_experiences*100:.1f}%)")

    print(f"\n{'='*80}")
    print(f"DESCRIPTION LENGTH ANALYSIS")
    print(f"{'='*80}")
    print(f"Experience descriptions:")
    print(f"  Average length: {avg_desc_length:.0f} characters")
    if description_lengths:
        print(f"  Shortest: {min(description_lengths)} chars")
        print(f"  Longest: {max(description_lengths)} chars")
    print(f"\nCompany descriptions:")
    print(f"  Average length: {avg_company_desc_length:.0f} characters")
    if company_desc_lengths:
        print(f"  Shortest: {min(company_desc_lengths)} chars")
        print(f"  Longest: {max(company_desc_lengths)} chars")

    # Sample experience descriptions
    print(f"\n{'='*80}")
    print(f"SAMPLE EXPERIENCE DESCRIPTIONS (First 5)")
    print(f"{'='*80}")
    for i, sample in enumerate(sample_descriptions[:5], 1):
        print(f"\n{i}. {sample['name']} - {sample['title']}")
        print(f"   Company: {sample['company']}")
        print(f"   Length: {sample['length']} chars")
        print(f"   Description: {sample['description']}")

    # Sample short descriptions
    if sample_short_descriptions:
        print(f"\n{'='*80}")
        print(f"SAMPLE SHORT DESCRIPTIONS (<{min_length_threshold} chars)")
        print(f"{'='*80}")
        for i, sample in enumerate(sample_short_descriptions, 1):
            print(f"\n{i}. {sample['name']} - {sample['title']}")
            print(f"   Company: {sample['company']}")
            print(f"   Length: {sample['length']} chars")
            print(f"   Description: {sample['description']}")

    # Sample company descriptions
    print(f"\n{'='*80}")
    print(f"SAMPLE COMPANY DESCRIPTIONS (First 5)")
    print(f"{'='*80}")
    for i, sample in enumerate(sample_company_descriptions[:5], 1):
        print(f"\n{i}. {sample['company']}")
        print(f"   Length: {sample['length']} chars")
        print(f"   Description: {sample['description']}")

    # Recommendation
    print(f"\n{'='*80}")
    print(f"RECOMMENDATION")
    print(f"{'='*80}")

    # Calculate percentages
    pct_with_substantial = (experiences_with_substantial_desc / total_experiences * 100) if total_experiences > 0 else 0
    pct_with_company = (experiences_with_company_desc / total_experiences * 100) if total_experiences > 0 else 0

    print(f"\nKey Metrics:")
    print(f"  • {experiences_with_substantial_desc:,} experiences ({pct_with_substantial:.1f}%) have substantial descriptions (>={min_length_threshold} chars)")
    print(f"  • {experiences_with_company_desc:,} experiences ({pct_with_company:.1f}%) have company descriptions")
    print(f"  • Average experience description length: {avg_desc_length:.0f} chars")
    print(f"  • Average company description length: {avg_company_desc_length:.0f} chars")

    print(f"\n{'='*50}")

    # Decision logic
    if pct_with_substantial >= 70:
        print("✅ SKIP COMPANY SCRAPING - Experience descriptions are sufficient")
        print(f"\nReason:")
        print(f"  • {pct_with_substantial:.1f}% of experiences have substantial descriptions")
        print(f"  • Average length of {avg_desc_length:.0f} chars provides detailed context")
        print(f"  • Company descriptions would be redundant")
        print(f"\n💰 Cost Savings: Skip company scraping to reduce API costs")

    elif pct_with_substantial >= 40 and avg_desc_length >= 80:
        print("⚠️  CONDITIONAL - Consider company scraping for experiences with short descriptions")
        print(f"\nReason:")
        print(f"  • {pct_with_substantial:.1f}% have substantial descriptions (moderate)")
        print(f"  • Could add logic: Only scrape company info when description < {min_length_threshold} chars")
        print(f"  • This would reduce scraping by ~{pct_with_substantial:.0f}%")
        print(f"\n💡 Implementation:")
        print(f"   if len(experience_description) < {min_length_threshold}:")
        print(f"       scrape_company_info()")

    else:
        print("❌ NEED COMPANY SCRAPING - Experience descriptions are insufficient")
        print(f"\nReason:")
        print(f"  • Only {pct_with_substantial:.1f}% have substantial descriptions")
        print(f"  • Average length of {avg_desc_length:.0f} chars is too short")
        print(f"  • Company descriptions ({avg_company_desc_length:.0f} chars avg) add significant value")
        print(f"\n📊 Worth the cost: Company data provides essential context")

if __name__ == "__main__":
    analyze_descriptions()
