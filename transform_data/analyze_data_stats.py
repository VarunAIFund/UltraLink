#!/usr/bin/env python3
import json
from collections import defaultdict, Counter
from typing import Dict, List, Any, Union
import os

def is_empty_value(value: Any) -> bool:
    """Check if a value is considered empty (None, empty string, empty list, etc.)"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False

def analyze_field_completeness(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Union[int, float]]]:
    """Analyze completeness of top-level fields"""
    total_records = len(data)
    field_stats = {}
    
    # Get all possible fields from all records
    all_fields = set()
    for record in data:
        all_fields.update(record.keys())
    
    for field in sorted(all_fields):
        filled_count = 0
        empty_count = 0
        
        for record in data:
            value = record.get(field)
            if is_empty_value(value):
                empty_count += 1
            else:
                filled_count += 1
        
        field_stats[field] = {
            'total_records': total_records,
            'filled': filled_count,
            'empty': empty_count,
            'fill_rate': (filled_count / total_records) * 100 if total_records > 0 else 0
        }
    
    return field_stats

def analyze_nested_arrays(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze nested array fields like experiences and educations"""
    array_fields = ['experiences', 'educations']
    nested_stats = {}
    
    for field in array_fields:
        lengths = []
        total_items = 0
        field_completeness = defaultdict(lambda: {'filled': 0, 'empty': 0})
        
        for record in data:
            field_value = record.get(field, [])
            if isinstance(field_value, list):
                lengths.append(len(field_value))
                total_items += len(field_value)
                
                # Analyze completeness of fields within each array item
                for item in field_value:
                    if isinstance(item, dict):
                        for subfield, subvalue in item.items():
                            if is_empty_value(subvalue):
                                field_completeness[subfield]['empty'] += 1
                            else:
                                field_completeness[subfield]['filled'] += 1
            else:
                lengths.append(0)
        
        # Calculate statistics
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        length_distribution = Counter(lengths)
        
        # Calculate fill rates for nested fields
        nested_field_stats = {}
        for subfield, counts in field_completeness.items():
            total = counts['filled'] + counts['empty']
            nested_field_stats[subfield] = {
                'filled': counts['filled'],
                'empty': counts['empty'],
                'total': total,
                'fill_rate': (counts['filled'] / total) * 100 if total > 0 else 0
            }
        
        nested_stats[field] = {
            'average_length': avg_length,
            'max_length': max(lengths) if lengths else 0,
            'min_length': min(lengths) if lengths else 0,
            'length_distribution': dict(length_distribution),
            'total_items': total_items,
            'records_with_data': sum(1 for l in lengths if l > 0),
            'records_without_data': sum(1 for l in lengths if l == 0),
            'nested_field_stats': nested_field_stats
        }
    
    return nested_stats

def generate_report(field_stats: Dict, nested_stats: Dict, total_records: int) -> str:
    """Generate a comprehensive text report"""
    report = []
    report.append("=" * 80)
    report.append("DATA COMPLETENESS ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Total Records Analyzed: {total_records:,}")
    report.append("")
    
    # Top-level field analysis
    report.append("TOP-LEVEL FIELD COMPLETENESS")
    report.append("-" * 50)
    report.append(f"{'Field':<25} {'Filled':<8} {'Empty':<8} {'Fill Rate':<10}")
    report.append("-" * 50)
    
    # Sort fields by fill rate (descending)
    sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['fill_rate'], reverse=True)
    
    for field, stats in sorted_fields:
        report.append(f"{field:<25} {stats['filled']:<8} {stats['empty']:<8} {stats['fill_rate']:<10.1f}%")
    
    report.append("")
    
    # Summary statistics
    fill_rates = [stats['fill_rate'] for stats in field_stats.values()]
    report.append("SUMMARY STATISTICS")
    report.append("-" * 30)
    report.append(f"Average Fill Rate: {sum(fill_rates) / len(fill_rates):.1f}%")
    report.append(f"Best Fill Rate: {max(fill_rates):.1f}%")
    report.append(f"Worst Fill Rate: {min(fill_rates):.1f}%")
    report.append(f"Fields with 100% completion: {sum(1 for rate in fill_rates if rate == 100.0)}")
    report.append(f"Fields with 0% completion: {sum(1 for rate in fill_rates if rate == 0.0)}")
    report.append("")
    
    # Nested array analysis
    for field, stats in nested_stats.items():
        report.append(f"{field.upper()} ANALYSIS")
        report.append("-" * 50)
        report.append(f"Average items per record: {stats['average_length']:.1f}")
        report.append(f"Max items in a record: {stats['max_length']}")
        report.append(f"Min items in a record: {stats['min_length']}")
        report.append(f"Total items across all records: {stats['total_items']:,}")
        report.append(f"Records with data: {stats['records_with_data']:,} ({stats['records_with_data']/total_records*100:.1f}%)")
        report.append(f"Records without data: {stats['records_without_data']:,} ({stats['records_without_data']/total_records*100:.1f}%)")
        report.append("")
        
        # Length distribution
        report.append(f"{field.title()} Length Distribution:")
        for length, count in sorted(stats['length_distribution'].items()):
            percentage = (count / total_records) * 100
            report.append(f"  {length} items: {count:,} records ({percentage:.1f}%)")
        report.append("")
        
        # Nested field completeness
        if stats['nested_field_stats']:
            report.append(f"Field Completeness within {field.title()}:")
            report.append(f"{'Field':<20} {'Filled':<8} {'Empty':<8} {'Fill Rate':<10}")
            report.append("-" * 50)
            
            nested_sorted = sorted(stats['nested_field_stats'].items(), 
                                 key=lambda x: x[1]['fill_rate'], reverse=True)
            
            for subfield, substats in nested_sorted:
                report.append(f"{subfield:<20} {substats['filled']:<8} {substats['empty']:<8} {substats['fill_rate']:<10.1f}%")
        
        report.append("")
    
    return "\n".join(report)

def main():
    """Main analysis function"""
    input_file = "large_set_cleaned.json"
    output_file = "data_analysis_report.txt"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    print(f"Loading data from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("Error: Expected a list of records in the JSON file")
            return
        
        total_records = len(data)
        print(f"Loaded {total_records:,} records")
        
        # Analyze field completeness
        print("Analyzing field completeness...")
        field_stats = analyze_field_completeness(data)
        
        # Analyze nested arrays
        print("Analyzing nested arrays...")
        nested_stats = analyze_nested_arrays(data)
        
        # Generate report
        print("Generating report...")
        report = generate_report(field_stats, nested_stats, total_records)
        
        # Display report
        print("\n" + report)
        
        # Save report to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nDetailed report saved to: {output_file}")
        
        # Quick summary
        print(f"\nQUICK SUMMARY:")
        print(f"Total Records: {total_records:,}")
        print(f"Total Fields Analyzed: {len(field_stats)}")
        
        # Most and least complete fields
        sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['fill_rate'], reverse=True)
        if sorted_fields:
            best_field = sorted_fields[0]
            worst_field = sorted_fields[-1]
            print(f"Most Complete Field: {best_field[0]} ({best_field[1]['fill_rate']:.1f}%)")
            print(f"Least Complete Field: {worst_field[0]} ({worst_field[1]['fill_rate']:.1f}%)")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()