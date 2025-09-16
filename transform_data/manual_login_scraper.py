#!/usr/bin/env python3
"""
Manual Login LinkedIn Scraper

Opens browser, waits for you to sign in, then captures redirects
"""

import csv
import os
import random
import time
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_chrome_driver():
    """Setup Chrome driver for manual login"""
    print("🚀 Setting up Chrome driver...")
    
    # Chrome options - make it obvious this is for manual use
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--start-maximized")  # Start maximized for easy use
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    print("✅ Chrome browser opened")
    return driver

def manual_login_wait(driver):
    """Wait for manual login with automatic countdown"""
    print("🌐 Opening LinkedIn for manual login...")
    driver.get("https://www.linkedin.com/login")
    
    print("\n" + "="*60)
    print("👆 PLEASE LOG IN TO LINKEDIN IN THE BROWSER WINDOW")
    print("="*60)
    print("1. Enter your LinkedIn email and password")
    print("2. Complete any 2FA/security checks")  
    print("3. Make sure you reach your LinkedIn homepage/feed")
    print("")
    print("⏱️ You have 60 seconds to log in (more time for processing many URLs)...")
    print("="*60)
    
    # Countdown timer - increased to 60 seconds for batch processing
    for i in range(60, 0, -1):
        print(f"⏱️ {i:2d} seconds remaining to log in...", end='\r')
        time.sleep(1)
    
    print("\n⏰ Time's up! Checking login status...")
    
    # Verify we're logged in
    current_url = driver.current_url
    print(f"🔍 Current URL: {current_url}")
    
    if "feed" in current_url or "hp" in current_url:
        print("✅ Login successful! Ready to test redirects.")
        return True
    elif "login" not in current_url and "linkedin.com" in current_url:
        print("✅ Looks like you're logged in! Ready to test redirects.")
        return True
    else:
        print("⚠️ Still on login page, but continuing anyway...")
        return False

def test_company_redirect(driver, url: str) -> str:
    """Test a single company URL redirect"""
    print(f"\n📡 Testing redirect for: {url}")
    
    # Navigate to the company URL
    print("🌐 Navigating to company page...")
    driver.get(url)
    
    # Wait for any redirects to complete with random timing
    redirect_wait = random.uniform(4, 8)  # Random wait between 4-8 seconds
    print(f"⏱️ Waiting {redirect_wait:.1f} seconds for redirects...")
    time.sleep(redirect_wait)
    
    # Get the final URL
    final_url = driver.current_url
    
    # Clean up URL (remove query parameters)
    if '?' in final_url:
        clean_final_url = final_url.split('?')[0]
    else:
        clean_final_url = final_url
    
    clean_final_url = clean_final_url.rstrip('/')
    original_clean = url.rstrip('/')
    
    print(f"🔍 Original URL: {original_clean}")
    print(f"🔍 Final URL:    {clean_final_url}")
    
    if clean_final_url != original_clean:
        print(f"✅ REDIRECT FOUND!")
        print(f"   {original_clean}")
        print(f"   ↓")
        print(f"   {clean_final_url}")
    else:
        print(f"📍 No redirect - URL stayed the same")
    
    return clean_final_url

def save_single_result(original_url: str, final_url: str, filename: str = "linkedin_redirects.csv"):
    """Append a single result to the CSV file immediately"""
    # Check if file exists to decide whether to write header
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header only if file doesn't exist
        if not file_exists:
            writer.writerow(['alternate_url', 'url'])
            print(f"📁 Created new CSV file: {filename}")
        
        # Write the result immediately
        writer.writerow([original_url, final_url])
        print(f"💾 Added to CSV: {original_url} → {final_url}")


def process_urls(driver, urls: List[str]) -> Dict[str, str]:
    """Process all URLs and capture redirects with real-time CSV saving"""
    print(f"\n🔄 Testing {len(urls)} URLs for redirects...")
    print(f"⏱️ Estimated time: {len(urls) * 8 // 60} minutes ({len(urls) * 8} seconds)")
    print("💾 Each result will be added to CSV immediately!")
    
    results = {}
    
    for i, url in enumerate(urls):
        print(f"\n--- URL {i+1}/{len(urls)} ---")
        
        final_url = test_company_redirect(driver, url.rstrip('/'))
        clean_original = url.rstrip('/')
        results[clean_original] = final_url
        
        # Save this result to CSV immediately
        save_single_result(clean_original, final_url)
        
        # Progress milestone every 5 URLs
        if (i + 1) % 5 == 0:
            print(f"📊 Progress milestone: {i+1}/{len(urls)} URLs completed")
        
        # Wait between URLs with random timing to appear more human
        if i < len(urls) - 1:
            wait_time = random.uniform(3, 7)  # Random delay between 3-7 seconds
            print(f"⏱️ Waiting {wait_time:.1f} seconds before next URL...")
            time.sleep(wait_time)
        
        # Give a progress update every 10 URLs
        if (i + 1) % 10 == 0:
            remaining = len(urls) - (i + 1)
            est_time = remaining * 8 // 60
            print(f"📊 Progress: {i+1}/{len(urls)} completed, ~{remaining} remaining (~{est_time} minutes)")
    
    return results

def save_results(results: Dict[str, str]):
    """Save results to CSV"""
    filename = "linkedin_redirects.csv"
    print(f"\n💾 Saving results to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['alternate_url', 'url'])
        
        for original, final in results.items():
            writer.writerow([original, final])
    
    print(f"✅ Saved {len(results)} results to {filename}")

def load_existing_results(filename: str = "linkedin_redirects.csv") -> set:
    """Load already processed URLs from existing CSV file"""
    processed_urls = set()
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 1:
                        processed_urls.add(row[0])  # Add the original URL
            
            print(f"📋 Found {len(processed_urls)} already processed URLs in {filename}")
        except Exception as e:
            print(f"⚠️ Could not read existing results: {e}")
    
    return processed_urls

def load_urls_from_file():
    """Load URLs from more_companies.txt file and filter out already processed ones"""
    file_path = os.path.join(os.path.dirname(__file__), "..", "apify", "more_companies.txt")
    
    try:
        with open(file_path, 'r') as f:
            all_urls = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"✅ Loaded {len(all_urls)} URLs from more_companies.txt")
        
        # Check for already processed URLs
        processed_urls = load_existing_results()
        
        # Filter out already processed URLs
        remaining_urls = []
        for url in all_urls:
            clean_url = url.rstrip('/')
            if clean_url not in processed_urls:
                remaining_urls.append(url)
            else:
                print(f"⏭️ Skipping already processed: {clean_url}")
        
        if len(remaining_urls) != len(all_urls):
            print(f"🔄 Resume mode: {len(remaining_urls)} URLs remaining out of {len(all_urls)} total")
        
        return remaining_urls
        
    except FileNotFoundError:
        print(f"❌ Could not find {file_path}")
        # Fallback to test URLs
        return [
            "https://www.linkedin.com/company/100780534/",
            "https://www.linkedin.com/company/104966180/",  
            "https://www.linkedin.com/company/107496897/"
        ]

def main():
    """Main function"""
    print("🔗 Manual LinkedIn Login & Redirect Scraper")
    print("="*50)
    
    # Load URLs from file
    urls = load_urls_from_file()
    
    # Check if there are any URLs to process
    if not urls:
        print("\n🎉 ALL DONE!")
        print("✅ All URLs have already been processed and are in linkedin_redirects.csv")
        print("📊 No additional work needed - all redirects captured!")
        return
    
    print("\nThis script will:")
    print("1. Open a Chrome browser")
    print("2. Wait for you to manually log in to LinkedIn")  
    print("3. Test each remaining URL to see where it redirects")
    print("4. Save the results to CSV")
    print("")
    
    driver = None
    try:
        # Setup browser
        driver = setup_chrome_driver()
        
        # Wait for manual login
        login_success = manual_login_wait(driver)
        
        # Process URLs even if login status unclear
        results = process_urls(driver, urls)
        
        # Show results summary
        print("\n" + "="*80)
        print("📊 REDIRECT RESULTS SUMMARY")
        print("="*80)
        
        redirect_count = 0
        for original, final in results.items():
            if original != final:
                print(f"✅ REDIRECT: {original} → {final}")
                redirect_count += 1
            else:
                print(f"📍 NO REDIRECT: {original}")
        
        print(f"\nTotal redirects found: {redirect_count}/{len(results)}")
        
        print(f"\n✅ All results have been saved to linkedin_redirects.csv in real-time!")
        print(f"📊 Final count: {len(results)} URLs processed successfully")
        
        print("\n⏱️ Keeping browser open for 10 seconds to review results...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        if driver:
            print("🧹 Closing browser...")
            driver.quit()
        print("✅ Done!")

if __name__ == "__main__":
    main()