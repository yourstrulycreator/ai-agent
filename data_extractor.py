import csv
import json
import os
from datetime import datetime
from ai_controller import AIController

class DataExtractor:
    def __init__(self, browser_agent):
        """Initialize the data extractor with a browser agent"""
        self.browser = browser_agent
        self.ai = AIController()
        
    def extract_profile_data(self, profile_url):
        """Extract data from a LinkedIn profile"""
        # Navigate to the profile
        self.browser.navigate_to(profile_url)
        
        # Get page content for AI to analyze
        page_content = self.browser.get_page_content()
        
        # Extract basic profile information using standard selectors
        # These are common selectors for LinkedIn profiles, but they may need to be updated
        data = {
            "name": self._extract_text(self.ai.fallback_selectors("name")),
            "title": self._extract_text(self.ai.fallback_selectors("job_title")),
            "company": self._extract_text(self.ai.fallback_selectors("company")),
            "location": self._extract_text(self.ai.fallback_selectors("location")),
            "url": profile_url,
            "timestamp": datetime.now().isoformat()
        }
        
        # If standard selectors fail, try to use AI to find elements
        if not data["name"]:
            ai_selector = self.ai.identify_elements(page_content, "name")
            data["name"] = self._extract_text(ai_selector)
            
        if not data["title"]:
            ai_selector = self.ai.identify_elements(page_content, "job_title")
            data["title"] = self._extract_text(ai_selector)
            
        if not data["company"]:
            ai_selector = self.ai.identify_elements(page_content, "company")
            data["company"] = self._extract_text(ai_selector)
            
        if not data["location"]:
            ai_selector = self.ai.identify_elements(page_content, "location")
            data["location"] = self._extract_text(ai_selector)
        
        return data

    def extract_people_data(self, people_url):
        """Extract people data from a LinkedIn school's people page using improved AI analysis"""
        # Navigate to the URL
        self.browser.navigate_to(people_url)
        print(f"Navigated to school people page: {people_url}")
        
        # Take a screenshot to analyze the page
        debug_file = "page_initial_view.png"
        self.browser.take_screenshot(debug_file)
        print(f"Initial page screenshot saved to {debug_file}")
        
        # Scroll down to load more profiles
        print("Scrolling to load more profiles...")
        for i in range(3):  # Scroll down 3 times
            self.browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.browser.page.wait_for_timeout(2000)  # Wait 2 seconds after each scroll
            print(f"Scroll {i+1} completed")
        
        # Take another screenshot after scrolling
        debug_file2 = "page_after_scrolling.png"
        self.browser.take_screenshot(debug_file2)
        print(f"Post-scroll screenshot saved to {debug_file2}")
        
        # Get the page HTML for analysis
        page_html = self.browser.get_page_content()
        print("Analyzing page structure...")
        
        # Use AI to analyze the page structure
        try:
            # Get AI analysis of the page structure
            ai_analysis = self.ai.analyze_profile_containers(page_html)
            print(f"AI analysis results: {ai_analysis}")
            
            # Extract container and sub-element selectors from AI analysis
            container_selector = ai_analysis.get("container_selector", ".search-result__wrapper")
            
            # Let's try more specific selectors for alumni profiles
            potential_container_selectors = [
                # Common LinkedIn selectors for people in search results
                ".search-result__wrapper",
                ".reusable-search__result-container",
                ".org-people-profile-card",
                # More specific selectors for alumni pages
                ".search-result__occluded-item",
                "li.reusable-search__result-container"
            ]
            
            all_profiles = []
            profile_urls = []  # To store URLs for detailed profile visits
            
            # First pass: collect basic info and profile URLs
            for selector in potential_container_selectors:
                profile_containers = self.browser.page.query_selector_all(selector)
                print(f"Found {len(profile_containers)} profile containers with selector: {selector}")
                
                if profile_containers and len(profile_containers) > 0:
                    # Extract data from each container
                    for i, container in enumerate(profile_containers):
                        try:
                            # Look for people-specific elements to filter out non-people cards
                            # Most LinkedIn people cards have name, title, and often have connection info
                            name_selector = ".actor-name"
                            title_selector = ".search-result__info .subline-level-1"
                            
                            # Check alternative selectors if the default ones don't work
                            if not container.query_selector(name_selector):
                                name_selector = ".entity-result__title-text a"
                            
                            if not container.query_selector(title_selector):
                                title_selector = ".entity-result__primary-subtitle"
                            
                            name_el = container.query_selector(name_selector)
                            title_el = container.query_selector(title_selector)
                            
                            # Skip if no name found (likely not a person profile)
                            if not name_el:
                                continue
                                
                            name = name_el.inner_text().strip() if name_el else ""
                            title = title_el.inner_text().strip() if title_el else ""
                            
                            # Look for company/occupation information
                            company_selectors = [
                                ".search-result__info .subline-level-2", 
                                ".entity-result__secondary-subtitle"
                            ]
                            
                            company = ""
                            for company_selector in company_selectors:
                                company_el = container.query_selector(company_selector)
                                if company_el:
                                    company = company_el.inner_text().strip()
                                    break
                            
                            # Find the URL if possible
                            url = ""
                            link_selectors = [
                                "a.app-aware-link",  # Specific to profile links
                                ".actor-name a",
                                ".entity-result__title-text a",
                                ".artdeco-entity-lockup__title a"
                            ]
                            
                            for link_selector in link_selectors:
                                link_el = container.query_selector(link_selector)
                                if link_el:
                                    url = link_el.get_attribute("href") or ""
                                    # Filter out non-profile URLs
                                    if "/in/" in url:
                                        break
                            
                            # Filter out entries that don't look like people
                            if name and not any(term in name.lower() for term in ["university", "school", "online", "follow"]):
                                # Split name into first and last
                                name_parts = name.split()
                                first_name = name_parts[0] if name_parts else ""
                                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                                
                                profile = {
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "title": title,
                                    "employer": company,  # Initial employer from list view
                                    "linkedin_url": url,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                all_profiles.append(profile)
                                
                                # Save URL for detailed profile visit if available
                                if url and "/in/" in url:
                                    profile_urls.append((len(all_profiles) - 1, url))  # Store index and URL
                                
                                print(f"Extracted profile {i}: {name} - {title}")
                        except Exception as e:
                            print(f"Error extracting profile {i}: {e}")
                    
                    # If we found profiles with this selector, no need to try more
                    if all_profiles:
                        break
                
            # If we still didn't find any profiles, try the fallback method
            if not all_profiles:
                fallback_profiles = self._extract_profiles_by_direct_search()
                all_profiles.extend(fallback_profiles)
            
            # Second pass: Visit each profile page to get detailed information
            print(f"Found {len(profile_urls)} profile URLs for detailed extraction")
            max_profiles_to_visit = min(len(profile_urls), 20)  # Limit to prevent too many requests
            
            for idx, (profile_idx, url) in enumerate(profile_urls[:max_profiles_to_visit]):
                try:
                    print(f"Visiting profile {idx+1}/{max_profiles_to_visit}: {url}")
                    
                    # Navigate to the profile page
                    self.browser.navigate_to(url)
                    self.browser.page.wait_for_load_state("networkidle")
                    
                    # Wait for profile content to load
                    self.browser.page.wait_for_timeout(2000)
                    
                    # Extract detailed employer information
                    detailed_employer = self._extract_detailed_employer()
                    
                    # Update the profile with detailed information
                    if detailed_employer:
                        all_profiles[profile_idx]["employer"] = detailed_employer
                        print(f"Updated employer to: {detailed_employer}")
                    
                    # Make sure we have the correct URL
                    all_profiles[profile_idx]["linkedin_url"] = url
                    
                    # Take a screenshot of each profile for verification
                    profile_screenshot = f"profile_{profile_idx}.png"
                    self.browser.take_screenshot(profile_screenshot)
                    
                    # Navigate back to the list page
                    self.browser.navigate_to(people_url)
                    self.browser.page.wait_for_load_state("networkidle")
                    
                    # Allow time for the page to load
                    self.browser.page.wait_for_timeout(2000)
                    
                except Exception as e:
                    print(f"Error visiting profile {url}: {e}")
                    # Try to navigate back to the original page
                    try:
                        self.browser.navigate_to(people_url)
                        self.browser.page.wait_for_timeout(2000)
                    except:
                        pass
            
            print(f"Total profiles extracted: {len(all_profiles)}")
            return all_profiles
            
        except Exception as e:
            print(f"Error in profile extraction: {e}")
            return []

    def _extract_detailed_employer(self):
        """Extract detailed employer information from a profile page"""
        try:
            # Try different selectors for current position
            employer_selectors = [
                # Experience section - current position
                "section.experience-section li:first-child .pv-entity__secondary-title",
                # New LinkedIn layout
                "[data-field='experience_company_name']",
                # Alternative selector for experience
                ".pv-profile-section__list-item .pv-entity__company-summary-info h3",
                # More generic selector
                ".pv-position-entity .pv-entity__company-summary-info span:not(.visually-hidden)",
                # Very generic
                ".experience-section .pv-entity__company-summary-info"
            ]
            
            for selector in employer_selectors:
                try:
                    employer_el = self.browser.page.query_selector(selector)
                    if employer_el:
                        employer = employer_el.inner_text().strip()
                        if employer:
                            return employer
                except:
                    continue
            
            # Try to find the first experience entry as fallback
            experience_section = self.browser.page.query_selector("section#experience-section")
            if experience_section:
                first_entry = experience_section.query_selector("li.pv-entity__position-group-pager")
                if first_entry:
                    company_el = first_entry.query_selector(".pv-entity__company-summary-info span")
                    if company_el:
                        return company_el.inner_text().strip()
            
            return ""
        except Exception as e:
            print(f"Error extracting detailed employer: {e}")
            return ""

    def _extract_profile_from_container(self, container, index):
        """Extract profile data from a given container using Playwright methods"""
        try:
            # Use Playwright query selectors instead of Selenium-style find_element
            name_el = container.query_selector(".artdeco-entity-lockup__title")
            title_el = container.query_selector(".artdeco-entity-lockup__subtitle")
            company_el = container.query_selector(".artdeco-entity-lockup__caption")
            
            # Get the URL from the parent link if available
            url = ""
            parent_link = container.query_selector("ancestor::a")
            if parent_link:
                url = parent_link.get_attribute("href")
            
            # Extract text content
            name = name_el.inner_text() if name_el else ""
            title = title_el.inner_text() if title_el else ""
            company = company_el.inner_text() if company_el else ""
            
            # Debug info
            print(f"Profile {index}: Name={name}, Title={title}, Company={company}")
            
            return {
                "name": name,
                "title": title,
                "company": company,
                "url": url
            }
        except Exception as e:
            print(f"Error extracting from container {index}: {e}")
            return {}

    def _try_fallback_selectors(self):
        """Try a series of fallback selectors for finding LinkedIn profiles"""
        profiles = []
        
        # List of common LinkedIn profile card selectors
        fallback_selectors = [
            # Common selectors for search results and directory pages
            ".search-result__info",
            ".pv-browsemap-section__member-container",
            ".org-people-profile-card",
            ".org-people-profiles-module__profile-item",
            ".result-card",
            
            # Generic list items that might contain profiles
            "li.reusable-search__result-container",
            "li.artdeco-list__item",
            
            # Very generic container selectors as last resort
            ".artdeco-card",
            ".profile-content"
        ]
        
        for selector in fallback_selectors:
            try:
                elements = self.browser.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    print(f"Found {len(elements)} elements with fallback selector: {selector}")
                    
                    # Try to extract data from these elements
                    for i, element in enumerate(elements):
                        try:
                            # Look for text content that might be a name and title
                            texts = []
                            text_elements = element.query_selector_all("span, div, h3, p")
                            for text_el in text_elements:
                                text = text_el.inner_text().strip()
                                if text:
                                    texts.append(text)
                            
                            # Analyze the text content to identify name and title
                            # Usually the first non-empty text is the name, followed by title
                            if len(texts) >= 2:
                                name = texts[0]
                                title = texts[1]
                                company = texts[2] if len(texts) > 2 else ""
                                
                                # Split name into first and last
                                name_parts = name.split()
                                first_name = name_parts[0] if name_parts else ""
                                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                                
                                profile = {
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "title": title,
                                    "employer": company,
                                    "linkedin_url": "",
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                profiles.append(profile)
                                print(f"Extracted fallback profile: {name} - {title}")
                        except Exception as e:
                            print(f"Error extracting fallback profile {i}: {e}")
                    
                    # If we found profiles, no need to try more selectors
                    if profiles:
                        break
            except Exception as e:
                print(f"Error with fallback selector {selector}: {e}")
                
        return profiles

    def _wait_for_profiles(self):
        """Wait for profile elements to fully load on the page"""
        try:
            print("Waiting for profile elements to load...")
            # Wait for typical LinkedIn profile list elements with timeout
            selectors_to_try = [
                ".search-results-container",
                ".org-people-profiles-module__profile-list",
                ".artdeco-list",
                ".search-result__wrapper"
            ]
            
            found = False
            for selector in selectors_to_try:
                try:
                    # Wait up to 5 seconds for elements to appear
                    self.browser.page.wait_for_selector(selector, timeout=5000)
                    print(f"Found profiles with selector: {selector}")
                    found = True
                    break
                except:
                    continue
                    
            if not found:
                print("Warning: Could not detect profile elements on page")
                
            # Additional wait after finding elements
            self.browser.page.wait_for_timeout(2000)
            return found
        except Exception as e:
            print(f"Error waiting for profiles: {e}")
            return False

    def _is_valid_profile(self, name, url=""):
        """Check if an extracted item is likely a valid person profile"""
        if not name:
            return False
            
        # Filter out entries with organizational keywords
        org_keywords = ["university", "school", "online", "follow", "group", 
                    "department", "subsidiary", "service", "learning", "followers"]
        
        if any(keyword in name.lower() for keyword in org_keywords):
            return False
            
        # Check URL pattern for LinkedIn profile
        if url and not "/in/" in url:
            return False
            
        # Check for reasonable name length and structure
        if len(name.strip()) < 3 or len(name.split()) > 5:
            return False
            
        return True

    def _extract_profiles_by_direct_search(self):
        """Fallback method to extract profiles by searching for known elements directly using Playwright"""
        profiles = []
        try:
            # Try to find all profile cards using various selectors specific to LinkedIn alumni pages
            potential_selectors = [
                ".org-people-profile-card",
                ".search-result__info",
                ".artdeco-entity-lockup",
                ".pv-browsemap-section__member-container",
                ".pv-entity__position-group",
                ".artdeco-list__item"
            ]
            
            for selector in potential_selectors:
                elements = self.browser.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    for i, element in enumerate(elements):
                        try:
                            # Different pages have different structures, so try multiple sub-selectors
                            name_selectors = [
                                ".artdeco-entity-lockup__title", 
                                ".actor-name", 
                                ".search-result__title",
                                ".pv-entity__title"
                            ]
                            
                            title_selectors = [
                                ".artdeco-entity-lockup__subtitle", 
                                ".subline-level-1", 
                                ".search-result__subtitle",
                                ".pv-entity__secondary-title"
                            ]
                            
                            # Try to find the profile URL
                            url = ""
                            link_selectors = [
                                "a.app-aware-link",
                                "a.ember-view",
                                "a[data-control-name='search_srp_result']"
                            ]
                            
                            for link_selector in link_selectors:
                                link_el = element.query_selector(link_selector)
                                if link_el:
                                    potential_url = link_el.get_attribute("href")
                                    if potential_url and "/in/" in potential_url:
                                        url = potential_url
                                        break
                            
                            # Try each selector until we find something
                            name = ""
                            for name_selector in name_selectors:
                                name_el = element.query_selector(name_selector)
                                if name_el:
                                    name = name_el.inner_text().strip()
                                    break
                                    
                            title = ""
                            for title_selector in title_selectors:
                                title_el = element.query_selector(title_selector)
                                if title_el:
                                    title = title_el.inner_text().strip()
                                    break
                            
                            # Only add if we found at least a name
                            if name:
                                # Split name into first and last
                                name_parts = name.split()
                                first_name = name_parts[0] if name_parts else ""
                                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                                
                                profiles.append({
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "title": title,
                                    "employer": "",  # May need additional selectors
                                    "linkedin_url": url,
                                    "timestamp": datetime.now().isoformat()
                                })
                                print(f"Added profile: {name}")
                        except Exception as e:
                            print(f"Error processing element {i}: {e}")
                    
                    # If we found profiles with this selector, no need to try others
                    if profiles:
                        break
        except Exception as e:
            print(f"Error during direct search: {e}")
        
        return profiles

    def _extract_text(self, selector):
        """Extract text from an element using a CSS selector"""
        try:
            element = self.browser.page.query_selector(selector)
            if element:
                return element.inner_text()
            return ""
        except Exception as e:
            print(f"Error extracting {selector}: {e}")
            return ""
    
    def save_to_csv(self, data, filename):
        """Save extracted data to a CSV file, handling both single items and lists"""
        if not data:
            print("No data to save to CSV")
            return
            
        # Ensure data is a list
        data_list = data if isinstance(data, list) else [data]
        if not data_list:
            print("Empty data list, nothing to save to CSV")
            return
            
        # Get fieldnames from the first item
        fieldnames = data_list[0].keys() if data_list and isinstance(data_list[0], dict) else []
        if not fieldnames:
            print("No fields found in data, can't save to CSV")
            return
        
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header if file is empty or doesn't exist
            if not file_exists:
                writer.writeheader()
                
            # Write all records
            for item in data_list:
                writer.writerow(item)
                
            print(f"Data saved to CSV: {filename} ({len(data_list)} records)")
    
    def save_to_json(self, data, filename):
        """Save extracted data to a JSON file, handling both single items and lists"""
        try:
            # Ensure data is valid
            if not data:
                print("No data to save to JSON")
                return
                
            # Load existing data if file exists
            if os.path.isfile(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    try:
                        existing_data = json.load(file)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []
                
            # Ensure existing_data is a list
            if not isinstance(existing_data, list):
                existing_data = [existing_data]
                
            # Add new data to existing data
            if isinstance(data, list):
                existing_data.extend(data)
            else:
                existing_data.append(data)
            
            # Write back to file
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, indent=2, ensure_ascii=False)
                
            print(f"Data saved to JSON: {filename} ({len(existing_data)} total records)")
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")