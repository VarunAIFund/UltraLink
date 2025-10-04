#!/usr/bin/env python3
"""
Analyze Company Data Quality

Analyzes companies.json to determine field completeness, especially description, url, and tagline
"""

import json
import os
from collections import defaultdict, Counter

def analyze_company_data(input_file="../results/companies.json"):
    """Analyze company data quality and field completeness"""
    
    print(f"🔍 Analyzing company data quality: {input_file}")
    
    # Load company data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            companies = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    if not companies:
        print("❌ No companies found in file")
        return
    
    print(f"📊 Total companies loaded: {len(companies)}")
    
    # Key fields to analyze (especially description, url, tagline)
    priority_fields = ['description', 'url', 'tagline', 'companyName', 'websiteUrl', 'industry']
    all_fields = set()
    
    # Collect all possible fields
    for company in companies:
        all_fields.update(company.keys())
    
    # Analyze field completeness
    field_stats = {}
    
    for field in all_fields:
        filled = 0
        empty_values = 0
        null_values = 0
        missing_field = 0
        
        for company in companies:
            if field not in company:
                missing_field += 1
            else:
                value = company[field]
                if value is None:
                    null_values += 1
                elif value == "" or value == "N/A" or value == "n/a":
                    empty_values += 1
                else:
                    filled += 1
        
        total_empty = null_values + empty_values + missing_field
        fill_rate = (filled / len(companies)) * 100 if len(companies) > 0 else 0
        
        field_stats[field] = {
            'filled': filled,
            'null': null_values,
            'empty_string': empty_values,
            'missing': missing_field,
            'total_empty': total_empty,
            'fill_rate': fill_rate
        }
    
    # Print overall results
    print(f"\n" + "=" * 60)
    print(f"COMPANY DATA QUALITY ANALYSIS")
    print(f"=" * 60)
    print(f"Total Companies: {len(companies)}")
    
    # Priority fields analysis
    print(f"\n🎯 PRIORITY FIELDS ANALYSIS")
    print(f"-" * 40)
    
    for field in priority_fields:
        if field in field_stats:
            stats = field_stats[field]
            print(f"{field:<15}: {stats['fill_rate']:>6.1f}% filled ({stats['filled']}/{len(companies)})")
            if stats['total_empty'] > 0:
                empty_breakdown = []
                if stats['null'] > 0:
                    empty_breakdown.append(f"{stats['null']} null")
                if stats['empty_string'] > 0:
                    empty_breakdown.append(f"{stats['empty_string']} empty")
                if stats['missing'] > 0:
                    empty_breakdown.append(f"{stats['missing']} missing")
                print(f"{'':<15}  Empty: {', '.join(empty_breakdown)}")
    
    # All fields completeness
    print(f"\n📋 ALL FIELDS COMPLETENESS")
    print(f"-" * 40)
    
    # Sort by fill rate (worst first)
    sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['fill_rate'])
    
    for field, stats in sorted_fields:
        print(f"{field:<20}: {stats['fill_rate']:>6.1f}% ({stats['filled']}/{len(companies)})")
    
    # Critical field analysis
    critical_empty = []
    if 'description' in field_stats and field_stats['description']['total_empty'] > 0:
        critical_empty.append(f"description: {field_stats['description']['total_empty']} companies")
    if 'url' in field_stats and field_stats['url']['total_empty'] > 0:
        critical_empty.append(f"url: {field_stats['url']['total_empty']} companies")  
    if 'tagline' in field_stats and field_stats['tagline']['total_empty'] > 0:
        critical_empty.append(f"tagline: {field_stats['tagline']['total_empty']} companies")
    
    if critical_empty:
        print(f"\n⚠️  CRITICAL FIELDS WITH MISSING DATA:")
        for issue in critical_empty:
            print(f"  - {issue}")
    
    # Sample companies with missing critical data
    print(f"\n🔍 SAMPLE COMPANIES WITH MISSING DATA:")
    print(f"-" * 40)
    
    # Find companies missing description
    missing_description = [c for c in companies if not c.get('description') or c.get('description') in [None, "", "N/A", "n/a"]]
    if missing_description:
        print(f"Missing description ({len(missing_description)} companies):")
        for company in missing_description[:3]:
            print(f"  - {company.get('companyName', 'Unknown')}: {company.get('url', 'No URL')}")
        if len(missing_description) > 3:
            print(f"    ... and {len(missing_description) - 3} more")
    
    # Find companies missing tagline
    missing_tagline = [c for c in companies if not c.get('tagline') or c.get('tagline') in [None, "", "N/A", "n/a"]]
    if missing_tagline:
        print(f"\nMissing tagline ({len(missing_tagline)} companies):")
        for company in missing_tagline[:3]:
            print(f"  - {company.get('companyName', 'Unknown')}: {company.get('tagline', 'No tagline')}")
        if len(missing_tagline) > 3:
            print(f"    ... and {len(missing_tagline) - 3} more")
    
    # Find companies missing url
    missing_url = [c for c in companies if not c.get('url') or c.get('url') in [None, "", "N/A", "n/a"]]
    if missing_url:
        print(f"\nMissing URL ({len(missing_url)} companies):")
        for company in missing_url[:3]:
            print(f"  - {company.get('companyName', 'Unknown')}: {company.get('input_linkedin_url', 'No input URL')}")
        if len(missing_url) > 3:
            print(f"    ... and {len(missing_url) - 3} more")
    
    # Description word count analysis
    if 'description' in field_stats:
        description_word_counts = []
        descriptions_with_content = []
        
        for company in companies:
            description = company.get('description')
            if description and description not in [None, "", "N/A", "n/a"]:
                word_count = len(description.split())
                description_word_counts.append(word_count)
                descriptions_with_content.append({
                    'company': company.get('companyName', 'Unknown'),
                    'word_count': word_count,
                    'description': description[:100] + "..." if len(description) > 100 else description
                })
        
        if description_word_counts:
            avg_words = sum(description_word_counts) / len(description_word_counts)
            min_words = min(description_word_counts)
            max_words = max(description_word_counts)
            
            print(f"\n📝 DESCRIPTION WORD COUNT ANALYSIS:")
            print(f"  Companies with descriptions: {len(description_word_counts)}")
            print(f"  Average words per description: {avg_words:.1f}")
            print(f"  Shortest description: {min_words} words")
            print(f"  Longest description: {max_words} words")
            
            # Show examples
            sorted_descriptions = sorted(descriptions_with_content, key=lambda x: x['word_count'])
            print(f"\n  Shortest descriptions:")
            for desc in sorted_descriptions[:3]:
                print(f"    {desc['company']}: {desc['word_count']} words - \"{desc['description']}\"")
            
            print(f"\n  Longest descriptions:")
            for desc in sorted_descriptions[-3:]:
                print(f"    {desc['company']}: {desc['word_count']} words - \"{desc['description']}\"")

    # Industry distribution
    if 'industry' in field_stats:
        industries = Counter()
        for company in companies:
            industry = company.get('industry')
            if industry and industry not in [None, "", "N/A", "n/a"]:
                industries[industry] += 1
        
        if industries:
            print(f"\n🏭 TOP INDUSTRIES:")
            for industry, count in industries.most_common(10):
                print(f"  {industry}: {count} companies")
    
    # Overall quality score
    priority_avg = sum(field_stats[f]['fill_rate'] for f in priority_fields if f in field_stats) / len([f for f in priority_fields if f in field_stats])
    overall_avg = sum(stats['fill_rate'] for stats in field_stats.values()) / len(field_stats)
    
    print(f"\n📈 QUALITY SCORES")
    print(f"-" * 40)
    print(f"Priority fields average: {priority_avg:.1f}%")
    print(f"Overall fields average: {overall_avg:.1f}%")
    
    if priority_avg >= 90:
        quality_rating = "Excellent"
    elif priority_avg >= 75:
        quality_rating = "Good"
    elif priority_avg >= 60:
        quality_rating = "Fair"
    else:
        quality_rating = "Poor"
    
    print(f"Data quality rating: {quality_rating}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if 'description' in field_stats and field_stats['description']['fill_rate'] < 80:
        print(f"  - Focus on collecting company descriptions ({field_stats['description']['total_empty']} missing)")
    if 'tagline' in field_stats and field_stats['tagline']['fill_rate'] < 70:
        print(f"  - Improve tagline collection ({field_stats['tagline']['total_empty']} missing)")  
    if 'url' in field_stats and field_stats['url']['fill_rate'] < 95:
        print(f"  - Verify URL collection process ({field_stats['url']['total_empty']} missing)")
    
    print(f"\n" + "=" * 60)

def main():
    """Main function"""
    print("🏢 Company Data Quality Analyzer")
    print("=" * 50)
    
    analyze_company_data()

if __name__ == "__main__":
    main()