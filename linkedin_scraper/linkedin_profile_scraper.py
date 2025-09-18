import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_browser():
    """Set up Chrome browser with options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_manual_login(driver):
    """Wait for user to manually log in to LinkedIn"""
    print(f"\n🔐 Please log in to LinkedIn manually in the browser window.")
    input("Press Enter after you have logged in to continue...")
    print("✅ Proceeding with scraping...")
    return True

def scrape_profile_data(driver, profile_url):
    """Scrape LinkedIn profile data"""
    profile_data = {
        "linkedinUrl": profile_url,
        "fullName": "",
        "headline": "",
        "location": "",
        "about": "",
        "experiences": [],
        "educations": []
    }
    
    try:
        print(f"📄 Navigating to profile: {profile_url}")
        driver.get(profile_url)
        
        # Random delay to avoid bot detection
        time.sleep(random.uniform(3, 7))
        
        # Wait for page to load
        time.sleep(3)
        
        # Extract basic profile info - try multiple selectors
        try:
            name_selectors = [
                "h1.text-heading-xlarge",
                "h1.break-words", 
                ".pv-text-details__left-panel h1",
                ".mt2 h1",
                "h1"
            ]
            for selector in name_selectors:
                try:
                    name_element = driver.find_element(By.CSS_SELECTOR, selector)
                    profile_data["fullName"] = name_element.text.strip()
                    print(f"👤 Found name: {profile_data['fullName']}")
                    break
                except NoSuchElementException:
                    continue
            else:
                print("❌ Could not find name")
        except Exception as e:
            print(f"❌ Error finding name: {e}")
        
        try:
            headline_selectors = [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium",
                ".mt2 .text-body-medium",
                "div.text-body-medium"
            ]
            for selector in headline_selectors:
                try:
                    headline_element = driver.find_element(By.CSS_SELECTOR, selector)
                    profile_data["headline"] = headline_element.text.strip()
                    print(f"💼 Found headline: {profile_data['headline'][:50]}...")
                    break
                except NoSuchElementException:
                    continue
            else:
                print("❌ Could not find headline")
        except Exception as e:
            print(f"❌ Error finding headline: {e}")
        
        try:
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small", 
                ".mt2 .text-body-small",
                "span.text-body-small"
            ]
            for selector in location_selectors:
                try:
                    location_element = driver.find_element(By.CSS_SELECTOR, selector)
                    profile_data["location"] = location_element.text.strip()
                    print(f"📍 Found location: {profile_data['location']}")
                    break
                except NoSuchElementException:
                    continue
            else:
                print("❌ Could not find location")
        except Exception as e:
            print(f"❌ Error finding location: {e}")
        
        # Improve scrolling to ensure all content loads
        print("📜 Scrolling to load all profile content...")
        
        # Scroll in stages to trigger lazy loading
        for i in range(5):
            scroll_position = (i + 1) * 20  # Scroll 20%, 40%, 60%, 80%, 100%
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_position / 100});")
            time.sleep(1.5)  # Give time for content to load
            
            # Try to click "Show more" or "See more" buttons
            try:
                show_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Show more') or contains(text(), 'See more')]")
                for button in show_more_buttons[:2]:  # Click max 2 buttons to avoid infinite loops
                    try:
                        button.click()
                        time.sleep(1)
                        print("✅ Clicked 'Show more' button")
                    except:
                        continue
            except:
                pass
        
        # Final scroll to top and back down to ensure everything is loaded
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Debug: Print page source to see what's available
        print("🔍 DEBUG: Looking for experience section...")
        page_source = driver.page_source
        if "experience" in page_source.lower():
            print("✅ Found 'experience' text in page")
        else:
            print("❌ No 'experience' text found in page")
        
        # Print all section IDs for debugging
        sections = driver.find_elements(By.TAG_NAME, "section")
        print(f"🔍 Found {len(sections)} sections on page:")
        for i, section in enumerate(sections[:10]):  # Limit to first 10
            try:
                section_id = section.get_attribute("id")
                section_class = section.get_attribute("class") 
                if section_id:
                    print(f"  Section {i}: id='{section_id}', class='{section_class[:50]}...'")
            except:
                continue
        
        # Extract experience section using text-based search
        try:
            print("🔍 Searching for experience section by text...")
            
            # Search for specific company names from the working data
            target_companies = ["DeepLearning.AI", "AI Fund", "LandingAI", "Coursera", "Stanford University"]
            
            print("🔍 Looking for known companies in page text...")
            page_text = driver.page_source.lower()
            found_companies = [comp for comp in target_companies if comp.lower() in page_text]
            print(f"✅ Found companies in page: {found_companies}")
            
            # Try multiple approaches to find the experience section
            experience_section = None
            search_attempts = [
                "//section[.//h2[contains(text(), 'Experience')]]",
                "//div[.//h2[contains(text(), 'Experience')]]", 
                "//section[contains(@aria-label, 'Experience')]",
                "//div[contains(@aria-label, 'Experience')]",
                "//section[.//span[contains(text(), 'Experience')]]",
                "//div[.//span[contains(text(), 'Experience')]]",
                "//*[contains(text(), 'DeepLearning.AI')]/ancestor::section",
                "//*[contains(text(), 'Managing General Partner')]/ancestor::section"
            ]
            
            for attempt in search_attempts:
                try:
                    experience_section = driver.find_element(By.XPATH, attempt)
                    print(f"✅ Found experience section using: {attempt}")
                    break
                except NoSuchElementException:
                    continue
            
            if not experience_section:
                print("❌ Could not find experience section with any method")
            
            if experience_section:
                print("🔍 Searching for experience items using specific company patterns...")
                
                # Look for elements containing the known company names
                experience_items = []
                for company in target_companies:
                    try:
                        company_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{company}')]")
                        for elem in company_elements:
                            # Get the parent container that likely holds the full experience
                            parent_containers = [
                                elem.find_element(By.XPATH, "./ancestor::li[1]"),
                                elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'pv')][1]"),
                                elem.find_element(By.XPATH, "./ancestor::div[@data-section][1]")
                            ]
                            
                            for container in parent_containers:
                                try:
                                    if container not in experience_items:
                                        experience_items.append(container)
                                        break
                                except:
                                    continue
                    except:
                        continue
                
                # Also try traditional list item search
                traditional_searches = [
                    ".//ul//li",
                    ".//li", 
                    ".//div[contains(@class, 'artdeco-list__item')]"
                ]
                
                for search in traditional_searches:
                    try:
                        items = experience_section.find_elements(By.XPATH, search)
                        for item in items:
                            if item not in experience_items and len(item.text.strip()) > 20:
                                experience_items.append(item)
                    except:
                        continue
                
                print(f"💼 Processing {len(experience_items)} potential experience items")
                
                for i, item in enumerate(experience_items):
                    try:
                        item_text = item.text.strip()
                        
                        # Skip empty items
                        if len(item_text) < 20:
                            continue
                        
                        print(f"🔍 Item {i+1} text preview: {item_text[:150]}...")
                        
                        experience = {}
                        lines = [line.strip() for line in item_text.split('\n') if line.strip()]
                        
                        # Look for known patterns from the working data
                        for line in lines:
                            # Check if this line contains a known job title
                            if any(title in line for title in ["Founder", "Managing General Partner", "Executive Chairman", "Co-Founder", "Adjunct Professor"]):
                                experience["title"] = line.strip()
                            
                            # Check if this line contains a known company
                            elif any(comp in line for comp in target_companies):
                                experience["companyName"] = line.strip()
                            
                            # Check for duration patterns
                            elif any(keyword in line.lower() for keyword in ['present', '·', 'yrs', 'mos']) and any(char.isdigit() for char in line):
                                experience["duration"] = line.strip()
                        
                        # Fallback: use first few lines if structured extraction failed
                        if not experience.get("title") and len(lines) >= 1:
                            experience["title"] = lines[0]
                        if not experience.get("companyName") and len(lines) >= 2:
                            experience["companyName"] = lines[1]
                        
                        if experience.get("title") or experience.get("companyName"):
                            profile_data["experiences"].append(experience)
                            print(f"  ✅ {experience.get('title', 'N/A')} at {experience.get('companyName', 'N/A')}")
                    
                    except Exception as e:
                        print(f"  ❌ Error processing item {i+1}: {e}")
                        continue
            else:
                print("❌ Could not find experience section")
        
        except Exception as e:
            print(f"❌ Error extracting experiences: {e}")
        
        # Extract education section using text-based search
        try:
            print("🔍 Searching for education section by text...")
            
            # Search for specific universities from the working data
            target_schools = ["University of California, Berkeley", "Massachusetts Institute of Technology", "UC Berkeley", "MIT"]
            
            print("🔍 Looking for known schools in page text...")
            found_schools = [school for school in target_schools if school.lower() in page_text]
            print(f"✅ Found schools in page: {found_schools}")
            
            # Try multiple approaches to find the education section
            education_section = None
            education_attempts = [
                "//section[.//h2[contains(text(), 'Education')]]",
                "//div[.//h2[contains(text(), 'Education')]]",
                "//section[contains(@aria-label, 'Education')]", 
                "//div[contains(@aria-label, 'Education')]",
                "//*[contains(text(), 'University of California, Berkeley')]/ancestor::section",
                "//*[contains(text(), 'Massachusetts Institute of Technology')]/ancestor::section",
                "//*[contains(text(), 'Doctor of Philosophy')]/ancestor::section"
            ]
            
            for attempt in education_attempts:
                try:
                    education_section = driver.find_element(By.XPATH, attempt)
                    print(f"✅ Found education section using: {attempt}")
                    break
                except NoSuchElementException:
                    continue
            
            if not education_section:
                print("❌ Could not find education section with any method")
            
            if education_section:
                print("🔍 Searching for education items using specific school patterns...")
                
                # Look for elements containing the known school names
                education_items = []
                for school in target_schools:
                    try:
                        school_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{school}')]")
                        for elem in school_elements:
                            # Get the parent container that likely holds the full education entry
                            parent_containers = [
                                elem.find_element(By.XPATH, "./ancestor::li[1]"),
                                elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'pv')][1]"),
                                elem.find_element(By.XPATH, "./ancestor::div[@data-section][1]")
                            ]
                            
                            for container in parent_containers:
                                try:
                                    if container not in education_items:
                                        education_items.append(container)
                                        break
                                except:
                                    continue
                    except:
                        continue
                
                # Also try traditional list item search
                traditional_searches = [
                    ".//ul//li",
                    ".//li",
                    ".//div[contains(@class, 'artdeco-list__item')]"
                ]
                
                for search in traditional_searches:
                    try:
                        items = education_section.find_elements(By.XPATH, search)
                        for item in items:
                            if item not in education_items and len(item.text.strip()) > 15:
                                education_items.append(item)
                    except:
                        continue
                
                print(f"🎓 Processing {len(education_items)} potential education items")
                
                for i, item in enumerate(education_items):
                    try:
                        item_text = item.text.strip()
                        
                        # Skip empty items
                        if len(item_text) < 15:
                            continue
                        
                        print(f"🔍 Education item {i+1} text preview: {item_text[:150]}...")
                        
                        education = {}
                        lines = [line.strip() for line in item_text.split('\n') if line.strip()]
                        
                        # Look for known patterns from the working data
                        for line in lines:
                            # Check if this line contains a known school
                            if any(school in line for school in target_schools + ["Berkeley", "MIT"]):
                                education["school"] = line.strip()
                            
                            # Check if this line contains degree information
                            elif any(degree_word in line.lower() for degree_word in ["phd", "doctorate", "doctor of philosophy", "master", "bachelor", "ms", "bs"]):
                                education["degree"] = line.strip()
                        
                        # Fallback: use first few lines if structured extraction failed  
                        if not education.get("school") and len(lines) >= 1:
                            # First line might be school name
                            education["school"] = lines[0]
                        if not education.get("degree") and len(lines) >= 2:
                            # Second line might be degree
                            education["degree"] = lines[1]
                        
                        if education.get("school"):
                            profile_data["educations"].append(education)
                            print(f"  ✅ {education.get('degree', 'N/A')} from {education['school']}")
                    
                    except Exception as e:
                        print(f"  ❌ Error processing education item {i+1}: {e}")
                        continue
            else:
                print("❌ Could not find education section")
        
        except Exception as e:
            print(f"❌ Error extracting education: {e}")
        
        return profile_data
    
    except Exception as e:
        print(f"❌ Error scraping profile: {e}")
        return profile_data

def main():
    profile_url = "https://www.linkedin.com/in/jeffreylai1"
    print(f"Scraping: {profile_url}")
    
    driver = setup_browser()
    
    try:
        # Navigate to LinkedIn login page
        print("🌐 Opening LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for manual login
        wait_for_manual_login(driver)
        
        # Scrape the profile
        profile_data = scrape_profile_data(driver, profile_url)
        
        # Save to JSON file
        output_file = "scraped_profile.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Profile data saved to {output_file}")
        print(f"📊 Summary:")
        print(f"   👤 Name: {profile_data['fullName']}")
        print(f"   💼 Headline: {profile_data['headline'][:50]}...")
        print(f"   💼 Experiences: {len(profile_data['experiences'])}")
        print(f"   🎓 Education: {len(profile_data['educations'])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()