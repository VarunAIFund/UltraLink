#!/usr/bin/env python3
"""
Evaluate Data Quality

Comprehensive data quality assessment and field completeness analysis for scraped LinkedIn profiles.
Analyzes fill rates, duplicate detection, experience completeness, and generates detailed quality reports.
"""

import json
import os
from collections import defaultdict, Counter

def load_scraped_data(filename="results/connections.json"):
    """Load scraped LinkedIn data"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []

def analyze_field_completeness(data):
    """Analyze completeness of key fields"""
    total_records = len(data)
    field_stats = {}
    
    # Key fields to analyze
    key_fields = [
        'fullName', 'headline', 'email', 'mobileNumber', 'linkedinUrl',
        'companyName', 'jobTitle', 'addressWithCountry', 'profilePic',
        'about', 'connections', 'followers'
    ]
    
    for field in key_fields:
        filled = 0
        for record in data:
            value = record.get(field)
            if value is not None and value != "" and value != 0:
                filled += 1
        
        fill_rate = (filled / total_records) * 100 if total_records > 0 else 0
        field_stats[field] = {
            'filled': filled,
            'empty': total_records - filled,
            'fill_rate': fill_rate
        }
    
    return field_stats

def analyze_experiences(data):
    """Analyze experience data quality"""
    total_profiles = len(data)
    profiles_with_exp = 0
    total_experiences = 0
    exp_field_stats = defaultdict(lambda: {'filled': 0, 'total': 0})
    
    for profile in data:
        experiences = profile.get('experiences', [])
        if experiences:
            profiles_with_exp += 1
            total_experiences += len(experiences)
            
            for exp in experiences:
                for field in ['title', 'subtitle', 'companyLink1', 'caption']:
                    exp_field_stats[field]['total'] += 1
                    if exp.get(field):
                        exp_field_stats[field]['filled'] += 1
    
    # Calculate fill rates
    for field, counts in exp_field_stats.items():
        if counts['total'] > 0:
            counts['fill_rate'] = (counts['filled'] / counts['total']) * 100
        else:
            counts['fill_rate'] = 0
    
    return {
        'profiles_with_experiences': profiles_with_exp,
        'total_experiences': total_experiences,
        'avg_experiences_per_profile': total_experiences / total_profiles if total_profiles > 0 else 0,
        'experience_coverage': (profiles_with_exp / total_profiles) * 100 if total_profiles > 0 else 0,
        'field_stats': dict(exp_field_stats)
    }

def analyze_contact_info(data):
    """Analyze contact information quality"""
    email_count = 0
    phone_count = 0
    both_count = 0
    
    for profile in data:
        has_email = profile.get('email') is not None and profile.get('email') != ""
        has_phone = profile.get('mobileNumber') is not None and profile.get('mobileNumber') != ""
        
        if has_email:
            email_count += 1
        if has_phone:
            phone_count += 1
        if has_email and has_phone:
            both_count += 1
    
    total = len(data)
    return {
        'email_coverage': (email_count / total) * 100 if total > 0 else 0,
        'phone_coverage': (phone_count / total) * 100 if total > 0 else 0,
        'both_contact_coverage': (both_count / total) * 100 if total > 0 else 0,
        'no_contact_count': total - max(email_count, phone_count)
    }

def analyze_company_data(data):
    """Analyze company information"""
    companies = Counter()
    industries = Counter()
    
    for profile in data:
        company = profile.get('companyName')
        industry = profile.get('companyIndustry')
        
        if company:
            companies[company] += 1
        if industry:
            industries[industry] += 1
    
    return {
        'unique_companies': len(companies),
        'top_companies': companies.most_common(10),
        'unique_industries': len(industries),
        'top_industries': industries.most_common(5)
    }

def analyze_duplicates(data):
    """Analyze duplicate LinkedIn URLs"""
    linkedin_urls = []
    for profile in data:
        url = profile.get('linkedinUrl')
        if url:
            linkedin_urls.append(url)
    
    unique_urls = set(linkedin_urls)
    duplicates = len(linkedin_urls) - len(unique_urls)
    
    return {
        'total_urls': len(linkedin_urls),
        'unique_urls': len(unique_urls),
        'duplicate_count': duplicates,
        'duplicate_rate': (duplicates / len(linkedin_urls)) * 100 if linkedin_urls else 0
    }

def generate_quality_report(data):
    """Generate comprehensive quality report"""
    total_records = len(data)
    
    print("=" * 60)
    print("LINKEDIN DATA QUALITY ASSESSMENT")
    print("=" * 60)
    print(f"Total Records: {total_records}")
    
    # Duplicate analysis
    dup_stats = analyze_duplicates(data)
    print(f"Unique LinkedIn URLs: {dup_stats['unique_urls']}")
    print(f"Duplicate URLs: {dup_stats['duplicate_count']}")
    if dup_stats['duplicate_count'] > 0:
        print(f"Duplicate rate: {dup_stats['duplicate_rate']:.1f}%")
    print()
    
    # Field completeness
    print("FIELD COMPLETENESS")
    print("-" * 40)
    field_stats = analyze_field_completeness(data)
    
    for field, stats in sorted(field_stats.items(), key=lambda x: x[1]['fill_rate'], reverse=True):
        print(f"{field:<20}: {stats['fill_rate']:>6.1f}% ({stats['filled']}/{total_records})")
    print()
    
    # Experience analysis
    print("EXPERIENCE DATA")
    print("-" * 40)
    exp_stats = analyze_experiences(data)
    print(f"Profiles with experiences: {exp_stats['profiles_with_experiences']} ({exp_stats['experience_coverage']:.1f}%)")
    print(f"Total experiences: {exp_stats['total_experiences']}")
    print(f"Avg experiences per profile: {exp_stats['avg_experiences_per_profile']:.1f}")
    print()
    
    if exp_stats['field_stats']:
        print("Experience field completeness:")
        for field, stats in exp_stats['field_stats'].items():
            print(f"  {field:<15}: {stats['fill_rate']:>6.1f}% ({stats['filled']}/{stats['total']})")
        print()
    
    # Contact information
    print("CONTACT INFORMATION")
    print("-" * 40)
    contact_stats = analyze_contact_info(data)
    print(f"Email coverage: {contact_stats['email_coverage']:.1f}%")
    print(f"Phone coverage: {contact_stats['phone_coverage']:.1f}%")
    print(f"Both email & phone: {contact_stats['both_contact_coverage']:.1f}%")
    print(f"No contact info: {contact_stats['no_contact_count']} profiles")
    print()
    
    # Company analysis
    print("COMPANY DATA")
    print("-" * 40)
    company_stats = analyze_company_data(data)
    print(f"Unique companies: {company_stats['unique_companies']}")
    print(f"Unique industries: {company_stats['unique_industries']}")
    print()
    
    print("Top companies:")
    for company, count in company_stats['top_companies']:
        print(f"  {company}: {count} profiles")
    print()
    
    print("Top industries:")
    for industry, count in company_stats['top_industries']:
        print(f"  {industry}: {count} profiles")
    print()
    
    # Overall quality score
    avg_fill_rate = sum(stats['fill_rate'] for stats in field_stats.values()) / len(field_stats)
    print("OVERALL ASSESSMENT")
    print("-" * 40)
    print(f"Average field completeness: {avg_fill_rate:.1f}%")
    
    if avg_fill_rate >= 80:
        quality_rating = "Excellent"
    elif avg_fill_rate >= 60:
        quality_rating = "Good"
    elif avg_fill_rate >= 40:
        quality_rating = "Fair"
    else:
        quality_rating = "Poor"
    
    print(f"Data quality rating: {quality_rating}")
    
    # Find and print example of profile without fullName
    print()
    print("SAMPLE RECORDS")
    print("-" * 40)
    
    missing_name_profile = None
    for profile in data:
        if not profile.get('fullName') or profile.get('fullName') == "":
            missing_name_profile = profile
            break
    
    if missing_name_profile:
        print("Example profile WITHOUT fullName:")
        print(json.dumps(missing_name_profile, indent=2)[:500] + "...")
    else:
        print("✅ All profiles have fullName field populated")
    
    print("=" * 60)

def main():
    """Main evaluation function"""
    data = load_scraped_data()
    
    if not data:
        print("No data to analyze")
        return
    
    generate_quality_report(data)

if __name__ == "__main__":
    main()