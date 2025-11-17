"""
Test the new structured search approach
"""
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from search_new import execute_search_new


def test_query(query: str):
    """Test a single query and display results"""
    print(f"\n{'='*100}")
    print(f"Query: {query}")
    print('='*100)

    try:
        result = execute_search_new(query)

        print(f"\n✓ Extracted Skills: {result['extracted_skills']}")
        print(f"✓ Extracted Seniority: {result['extracted_seniority']}")
        print(f"\n✓ Generated SQL:")
        print(result['sql'])
        print(f"\n✓ Total matching candidates: {result['total']}")
        print(f"✓ Returned in results: {result['returned']} (limited to 1000)")

        if result['total'] > 0:
            print(f"\n{'─'*100}")
            print("Top 5 Candidates:")
            print('─'*100)

            for i, candidate in enumerate(result['results'][:5], 1):
                print(f"\n{i}. {candidate['name']}")
                print(f"   LinkedIn: {candidate['linkedin_url']}")
                print(f"   Headline: {candidate['headline']}")
                print(f"   Location: {candidate['location']}")
                print(f"   Seniority: {candidate['seniority']}")
                print(f"   Years Experience: {candidate['years_experience']}")

                # Show matching skills
                if candidate['skills']:
                    matching_skills = [
                        skill for skill in candidate['skills']
                        if any(extracted.lower() in skill.lower() or skill.lower() in extracted.lower()
                               for extracted in result['extracted_skills'])
                    ]
                    if matching_skills:
                        print(f"   Matching Skills: {', '.join(matching_skills[:5])}")
                    else:
                        print(f"   Skills: {', '.join(candidate['skills'][:5])}")
        else:
            print("\n⚠ No candidates found. Try broadening your search criteria.")

        return result

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run a single test query"""

    # Accept query from command line or use default
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "Find Python developers"

    print("\n" + "="*100)
    print("TESTING NEW STRUCTURED SEARCH APPROACH")
    print("="*100)

    result = test_query(query)

    if result:
        # Save to JSON file
        output_file = os.path.join(os.path.dirname(__file__), 'test_search_new_results.json')
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'query': result['query'],
            'extracted_skills': result['extracted_skills'],
            'extracted_seniority': result['extracted_seniority'],
            'sql': result['sql'],
            'total_matching': result['total'],  # Actual total matching candidates
            'returned_count': result['returned'],  # Number returned (up to 1000)
            'results': result['results']  # Save ALL returned results
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
