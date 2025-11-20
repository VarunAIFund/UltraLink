#!/usr/bin/env python3
"""
UltraLink Data Collection Pipeline - Main Orchestrator

Runs the complete LinkedIn data collection and enrichment pipeline:
1. Scrape LinkedIn profiles from CSV connections
2. Extract company URLs from profiles
3. Scrape company data from LinkedIn
4. Enrich profiles with company descriptions
"""

import subprocess
import sys
import os

def run_script(script_path, description):
    """
    Run a Python script and handle errors

    Args:
        script_path: Path to the Python script to run
        description: Human-readable description of what the script does
    """
    print("\n" + "="*80)
    print(f"STEP: {description}")
    print("="*80 + "\n")

    try:
        # Run the script using subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            text=True
        )

        print(f"\n✅ {description} - COMPLETE")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ {description} - ERROR")
        print(f"Error: {e}")
        return False


def main():
    """
    Run the complete data collection pipeline
    """
    print("\n" + "="*80)
    print("ULTRALINK DATA COLLECTION PIPELINE")
    print("="*80)
    print("\nThis will run 3 sequential steps:")
    print("  1. Scrape LinkedIn profiles from CSV")
    print("  2. Extract company URLs from profiles")
    print("  3. Scrape company data")
    print("\n" + "="*80 + "\n")

    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Step 1: Scrape LinkedIn profiles
    # Use --auto flag to process all batches without prompting
    step1_result = subprocess.run(
        [sys.executable, os.path.join(current_dir, "get_data.py"), "--auto"],
        cwd=current_dir,
        check=False,
        text=True
    )

    step1 = (step1_result.returncode == 0)
    if step1:
        print(f"\n✅ 1/4: Scraping LinkedIn profiles - COMPLETE")
    else:
        print(f"\n❌ 1/4: Scraping LinkedIn profiles - FAILED")

    if not step1:
        print("\n❌ Pipeline stopped at step 1")
        return

    # Step 2: Extract company URLs
    step2 = run_script(
        os.path.join(current_dir, "get_companies", "extract_company_urls.py"),
        "2/4: Extracting company URLs"
    )

    if not step2:
        print("\n❌ Pipeline stopped at step 2")
        return

    # Step 3: Scrape companies
    # Use --auto flag to process all batches without prompting
    step3_result = subprocess.run(
        [sys.executable, os.path.join(current_dir, "get_companies", "scrape_companies.py"), "--auto"],
        cwd=current_dir,
        check=False,
        text=True
    )

    step3 = (step3_result.returncode == 0)
    if step3:
        print(f"\n✅ 3/4: Scraping company data - COMPLETE")
    else:
        print(f"\n❌ 3/4: Scraping company data - FAILED")

    if not step3:
        print("\n❌ Pipeline stopped at step 3")
        return

    # Step 4: Enrich connections (commented out)
    # step4 = run_script(
    #     os.path.join(current_dir, "enrich_connections_with_company_descriptions.py"),
    #     "4/4: Enriching profiles with company descriptions"
    # )

    # if not step4:
    #     print("\n❌ Pipeline stopped at step 4")
    #     return

    # All steps complete
    print("\n" + "="*80)
    print("🎉 PIPELINE COMPLETE!")
    print("="*80)
    print("\nAll data collection steps finished successfully.")
    print("Your LinkedIn profiles and company data have been scraped.")
    print("\nNext steps:")
    print("  - Review results in results/connections.json")
    print("  - Review company data in results/companies.json")
    print("  - Run transform_data pipeline for AI enhancement")
    print("  - Upload to Supabase database")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
