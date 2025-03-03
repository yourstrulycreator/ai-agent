import csv
import json
import os
import time  # Add this import
import random  # Add this import
from datetime import datetime
from ai_controller import AIController

class DataExtractor:
    def __init__(self, browser_agent):
        """Initialize the data extractor with a browser agent"""
        self.browser = browser_agent
        self.ai = AIController()
        
    def extract_people_data(self, people_url):
        """Extract people data from a LinkedIn school's people page using improved AI analysis"""
        # Navigate to the URL
        self.browser.navigate_to(people_url)
        print(f"Navigated to school people page: {people_url}")
        
        # Scroll down to load more profiles
        print("Scrolling to load more profiles...")
        for i in range(5):  # Scroll down 5 times
            self.browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.browser.page.wait_for_timeout(2000)  # Wait 2 seconds after each scroll
            print(f"Scroll {i+1} completed")
        
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
                "li.reusable-search__result-container",
                # Add more generic selectors to catch all types of profile containers
                "li.entity-result",
                "div.entity-result",
                "li.org-people-profile-card",
                "div.profile-card"
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
                            # Extract name and title as before
                            # Look for people-specific elements to filter out non-people cards
                            # Most LinkedIn people cards have name, title, and often have connection info
                            name_selector = ".actor-name"
                            title_selector = ".search-result__info .subline-level-1"
                            
                            # Check alternative selectors if the default ones don't work
                            if not container.query_selector(name_selector):
                                name_selector = ".entity-result__title-text a, .artdeco-entity-lockup__title a, .org-people-profile-card__profile-title a"
                            
                            if not container.query_selector(title_selector):
                                title_selector = ".entity-result__primary-subtitle, .artdeco-entity-lockup__subtitle, .org-people-profile-card__profile-position"
                            
                            name_el = container.query_selector(name_selector)
                            title_el = container.query_selector(title_selector)
                            
                            # Skip if no name found (likely not a person profile)
                            if not name_el:
                                continue
                                
                            name = name_el.inner_text().strip() if name_el else ""
                            title = title_el.inner_text().strip() if title_el else ""
                            
                            # Enhanced organization detection - check if this is an organization rather than a person
                            if self._is_organization(name, title, container):
                                print(f"Skipping organization: {name}")
                                continue
                            
                            # Look for company/occupation information
                            company_selectors = [
                                ".search-result__info .subline-level-2", 
                                ".entity-result__secondary-subtitle",
                                ".artdeco-entity-lockup__caption",
                                ".org-people-profile-card__profile-position-company"
                            ]
                            
                            company = ""
                            for company_selector in company_selectors:
                                company_el = container.query_selector(company_selector)
                                if company_el:
                                    company = company_el.inner_text().strip()
                                    break
                            
                            # New improved URL extraction method
                            url = self._extract_profile_url_from_container(container)
                            
                            if not url:
                                # Fallback to extract URL directly from HTML
                                try:
                                    html = container.evaluate("el => el.outerHTML")
                                    url = self._extract_profile_url_from_html(html)
                                except Exception as e:
                                    print(f"  Error extracting URL from HTML: {e}")
                            
                            # Split name into first and last
                            name_parts = name.split()
                            first_name = name_parts[0] if name_parts else ""
                            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                            
                            # Create profile with correct field structure
                            profile = {
                                "first_name": first_name,
                                "last_name": last_name,
                                "title": "",  # Empty title field that will be filled during profile visit
                                "description": title,  # Use the extracted title as description
                                "employer": company,
                                "linkedin_url": url,  # Store the properly formatted URL
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            all_profiles.append(profile)
                            
                            # Save URL for detailed profile visit if available
                            if url and "/in/" in url:
                                profile_urls.append((len(all_profiles) - 1, url))  # Store index and URL
                            
                            print(f"Extracted profile {i}: {first_name} {last_name} - {title} - URL: {url}")
                        except Exception as e:
                            print(f"Error extracting profile {i}: {e}")
                    
                    # If we found profiles with this selector, no need to try more
                    if all_profiles:
                        break
            
            # If we still didn't find any profiles or if URLs are missing, try the BeautifulSoup fallback method
            if not all_profiles or any(not profile.get("linkedin_url") for profile in all_profiles):
                print("Using BeautifulSoup fallback method to extract profile data")
                bs_profiles = self._extract_profiles_with_beautifulsoup(page_html)
                
                if not all_profiles:
                    # No profiles found with original method, use BS4 results
                    all_profiles = bs_profiles
                else:
                    # Merge results: update existing profiles with missing URLs
                    for i, profile in enumerate(all_profiles):
                        if not profile.get("linkedin_url") and i < len(bs_profiles) and bs_profiles[i].get("linkedin_url"):
                            profile["linkedin_url"] = bs_profiles[i]["linkedin_url"]
                            print(f"Updated missing URL for {profile['first_name']} {profile['last_name']} using BeautifulSoup")
                
                # Rebuild profile_urls list with the new/updated URLs
                profile_urls = []
                for i, profile in enumerate(all_profiles):
                    if profile.get("linkedin_url") and "/in/" in profile.get("linkedin_url", ""):
                        profile_urls.append((i, profile["linkedin_url"]))
            
            # If we still didn't find any profiles, try the original fallback method
            if not all_profiles:
                fallback_profiles = self._extract_profiles_by_direct_search()
                all_profiles.extend(fallback_profiles)
            
            # Second pass: Visit each profile page to get detailed information
            print(f"Found {len(profile_urls)} profile URLs for detailed extraction")
            max_profiles_to_visit = min(len(profile_urls), 150)  # Limit to prevent too many requests

            for idx, (profile_idx, url) in enumerate(profile_urls[:max_profiles_to_visit]):
                try:
                    # Validate URL before visiting
                    if not url.startswith(("http://", "https://")):
                        url = f"https://www.linkedin.com{url if url.startswith('/') else '/' + url}"
                    
                    print(f"Visiting profile {idx+1}/{max_profiles_to_visit}: {url}")
                    
                    # Make sure we have the correct URL in the profile data before attempting to visit
                    all_profiles[profile_idx]["linkedin_url"] = url
                    
                    # Set a flag to track if we've successfully visited the profile
                    profile_visited = False
                    
                    try:
                        # Navigate to the profile page with retry logic
                        max_retries = 3
                        for attempt in range(1, max_retries + 1):
                            try:
                                # Navigate to the profile page (without timeout parameter)
                                self.browser.navigate_to(url)
                                
                                # Wait for profile content to load
                                self.browser.page.wait_for_timeout(8000)  # Increased wait time to 8 seconds
                                
                                # Scroll down to trigger lazy loading of experience section
                                self.browser.page.evaluate("window.scrollBy(0, 500)")
                                self.browser.page.wait_for_timeout(3000)
                                
                                # Take a screenshot for debugging
                                #profile_screenshot = f"profile_{profile_idx}.png"
                                #self.browser.take_screenshot(profile_screenshot)
                                #print(f"Profile screenshot saved to {profile_screenshot}")
                                
                                # Mark as successfully visited
                                profile_visited = True
                                break
                                
                            except Exception as e:
                                if attempt < max_retries:
                                    wait_time = random.uniform(5, 15)
                                    print(f"Navigation error (attempt {attempt}/{max_retries}): {e}")
                                    print(f"Waiting {wait_time:.1f} seconds before retry...")
                                    time.sleep(wait_time)
                                else:
                                    print(f"Failed to navigate to profile after {max_retries} attempts: {e}")
                                    # Continue with partial data
                    
                    except Exception as e:
                        print(f"Error during profile navigation: {e}")
                    
                    # Only attempt extraction if we successfully visited the profile
                    if profile_visited:
                        try:
                            # Get page content for AI analysis
                            page_content = self.browser.get_page_content()
                            
                            # Use AI to extract detailed profile information
                            ai_profile_data = self.ai.analyze_profile_page(page_content)
                            
                            # Update profile with AI-extracted data
                            if ai_profile_data and isinstance(ai_profile_data, dict):
                                if ai_profile_data.get("job_title"):
                                    all_profiles[profile_idx]["title"] = ai_profile_data["job_title"]
                                    print(f"Updated title to: {ai_profile_data['job_title']}")
                                    
                                if ai_profile_data.get("employer"):
                                    all_profiles[profile_idx]["employer"] = ai_profile_data["employer"]
                                    print(f"Updated employer to: {ai_profile_data['employer']}")
                            
                            # If AI extraction failed, try direct extraction
                            if not all_profiles[profile_idx].get("title") or not all_profiles[profile_idx].get("employer"):
                                # Extract title from profile page using direct selectors
                                title_selectors = [
                                    ".text-heading-1",
                                    ".pv-top-card-section__headline",
                                    ".pv-text-details__left-panel .text-body-medium",
                                    "[data-field='headline']"
                                ]
                                
                                for title_selector in title_selectors:
                                    title_el = self.browser.page.query_selector(title_selector)
                                    if title_el:
                                        title_text = title_el.inner_text().strip()
                                        if title_text:
                                            all_profiles[profile_idx]["title"] = title_text
                                            print(f"Extracted title using selector: {title_text}")
                                            break
                                
                                # Extract detailed employer information
                                if not all_profiles[profile_idx].get("employer"):
                                    detailed_employer = self._extract_detailed_employer()
                                    if detailed_employer:
                                        all_profiles[profile_idx]["employer"] = detailed_employer
                                        print(f"Updated employer to: {detailed_employer}")
                            
                            # Try fallback extraction methods if needed
                            if hasattr(self, 'extract_job_title_from_profile') and not all_profiles[profile_idx].get("title"):
                                job_title = self.extract_job_title_from_profile(page_content)
                                if job_title:
                                    all_profiles[profile_idx]["title"] = job_title
                                    print(f"Extracted job title using fallback method: {job_title}")
                            
                            if hasattr(self, 'extract_employer_from_profile') and not all_profiles[profile_idx].get("employer"):
                                employer = self.extract_employer_from_profile(page_content)
                                if employer:
                                    all_profiles[profile_idx]["employer"] = employer
                                    print(f"Extracted employer using fallback method: {employer}")
                            
                        except Exception as e:
                            print(f"Error extracting data from profile: {e}")
                            # Continue with partial data
                    
                    # IMPORTANT: Save the profile data even if we couldn't extract everything
                    # This ensures we don't lose the data we already have
                    print(f"Saving profile data for {all_profiles[profile_idx]['first_name']} {all_profiles[profile_idx]['last_name']}")
                    
                    # Make sure output directory exists
                    os.makedirs("output", exist_ok=True)
                    
                    # Save individual profile data
                    self.save_to_csv([all_profiles[profile_idx]], "output/linkedin_data.csv")
                    self.save_to_json([all_profiles[profile_idx]], "output/linkedin_data.json")
                    
                    try:
                        # Navigate back to the list page
                        self.browser.navigate_to(people_url)
                        # Don't wait for networkidle, just use a fixed timeout
                        self.browser.page.wait_for_timeout(5000)
                    except Exception as e:
                        print(f"Error navigating back to people page: {e}")
                        # Try one more time with a longer timeout
                        try:
                            self.browser.navigate_to(people_url)
                            self.browser.page.wait_for_timeout(10000)
                        except:
                            print("Failed to navigate back to people page after retry")
                    
                except Exception as e:
                    print(f"Error processing profile {url}: {e}")
                    # Try to navigate back to the original page
                    try:
                        self.browser.navigate_to(people_url)
                        self.browser.page.wait_for_timeout(5000)
                    except:
                        pass
            
            print(f"Total profiles extracted: {len(all_profiles)}")
            return all_profiles
            
        except Exception as e:
            print(f"Error in profile extraction: {e}")
            return []
    
    def _extract_profile_url_from_container(self, container):
        """Extract LinkedIn profile URL from a container element with improved detection"""
        url = ""
        # Try specific LinkedIn profile link selectors
        link_selectors = [
            "a.app-aware-link[href*='/in/']",
            "a[id^='org-people-profile-card__profile-image-']",
            "a[data-test-app-aware-link]",
            ".entity-result__title-text a",
            ".artdeco-entity-lockup__title a",
            ".search-result__result-link",
            ".search-result__info a",
            "a[data-control-name='search_srp_result']",
            # Add more generic selectors that might contain profile links
            "a[href*='/in/']",
            "a.artdeco-entity-lockup__link",
            "a.app-aware-link"
        ]
        
        print(f"Trying to extract URL from container")
        for link_selector in link_selectors:
            link_elements = container.query_selector_all(link_selector)
            print(f"  Selector '{link_selector}' found {len(link_elements)} elements")
            
            for link_el in link_elements:
                try:
                    href = link_el.get_attribute("href")
                    print(f"  Found href: {href}")
                    if href and self._is_valid_linkedin_profile_url(href):
                        url = self._normalize_linkedin_url(href)
                        print(f"  Extracted URL: {url}")
                        return url
                except Exception as e:
                    print(f"  Error getting href: {e}")
        
        # If no URL found with specific selectors, try all links
        if not url:
            print("  No URL found with specific selectors, trying all links")
            all_links = container.query_selector_all("a")
            print(f"  Found {len(all_links)} total links")
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    print(f"  Checking link: {href}")
                    if href and self._is_valid_linkedin_profile_url(href):
                        url = self._normalize_linkedin_url(href)
                        print(f"  Found URL from general links: {url}")
                        return url
                except Exception as e:
                    print(f"  Error checking link: {e}")
        
        return url
    
    def _extract_profile_url_from_html(self, html):
        """Extract LinkedIn profile URL from HTML content using regex"""
        import re
        url_patterns = [
            r'href="(https?://(?:www\.)?linkedin\.com/in/[^"]+)"',
            r'href="(/in/[^"]+)"',
            r'href=[\'"]([^\'"]*\/in\/[^\'"]*)[\'"]'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, html)
            if matches:
                for match in matches:
                    if self._is_valid_linkedin_profile_url(match):
                        return self._normalize_linkedin_url(match)
        
        return ""
    
    def _extract_profiles_with_beautifulsoup(self, html):
        """Extract profile data using BeautifulSoup as a fallback method"""
        from bs4 import BeautifulSoup
        import re
        
        print("Extracting profiles with BeautifulSoup")
        
        soup = BeautifulSoup(html, 'html.parser')
        profiles = []
        
        # Look for common profile card containers based on the example provided
        profile_containers = []
        
        # Try to find profile cards based on the example structure
        profile_containers.extend(soup.select("li.org-people-profile-card__profile-card-spacing"))
        profile_containers.extend(soup.select("li.grid"))
        profile_containers.extend(soup.select("section.artdeco-card"))
        
        # If not found, try more generic containers
        if not profile_containers:
            profile_containers.extend(soup.select("li.reusable-search__result-container"))
            profile_containers.extend(soup.select("li.search-result"))
            profile_containers.extend(soup.select("li.entity-result"))
        
        print(f"Found {len(profile_containers)} potential profile containers with BeautifulSoup")
        
        # Process each container
        for i, container in enumerate(profile_containers):
            try:
                # Find profile URL - first look in expected locations based on the example
                url = ""
                
                # Check for profile links with specific attributes from the example
                profile_links = container.select("a[href*='/in/']")
                profile_links.extend(container.select("a.app-aware-link"))
                profile_links.extend(container.select("a[data-test-app-aware-link]"))
                
                # Try specific profile image selector from example
                if not profile_links:
                    img_container = container.select_one("a[id^='org-people-profile-card__profile-image-']")
                    if img_container:
                        profile_links = [img_container]
                
                # Look for links in lockup titles
                if not profile_links:
                    title_links = container.select(".artdeco-entity-lockup__title a")
                    profile_links.extend(title_links)
                
                # Extract href from the first valid profile link
                for link in profile_links:
                    if link.has_attr('href') and ('/in/' in link['href'] or 'linkedin.com/in/' in link['href']):
                        url = self._normalize_linkedin_url(link['href'])
                        break
                
                # If no URL found yet, try regex on container HTML
                if not url:
                    container_html = str(container)
                    url_matches = re.findall(r'href=[\'"]([^\'"]*(?:\/in\/|linkedin\.com\/in\/)[^\'"]*)[\'"]', container_html)
                    if url_matches:
                        url = self._normalize_linkedin_url(url_matches[0])
                
                # Find name
                name = ""
                name_elements = []
                
                # Try lockup title first (from example)
                name_containers = container.select(".artdeco-entity-lockup__title")
                for name_container in name_containers:
                    text = name_container.get_text(strip=True)
                    if text and len(text) > 1:  # Avoid empty or single character names
                        name = text
                        break
                
                # Other common name selectors
                if not name:
                    name_selectors = [
                        ".entity-result__title-text",
                        ".actor-name",
                        ".search-result__title",
                        ".org-people-profile-card__profile-title"
                    ]
                    
                    for selector in name_selectors:
                        name_element = container.select_one(selector)
                        if name_element:
                            name = name_element.get_text(strip=True)
                            if name:
                                break
                
                # Extract title/description
                title = ""
                title_elements = container.select(".artdeco-entity-lockup__subtitle")
                if title_elements:
                    title = title_elements[0].get_text(strip=True)
                
                if not title:
                    # Try other common title selectors
                    title_selectors = [
                        ".entity-result__primary-subtitle",
                        ".search-result__info .subline-level-1",
                        ".pv-entity__secondary-title"
                    ]
                    
                    for selector in title_selectors:
                        title_element = container.select_one(selector)
                        if title_element:
                            title = title_element.get_text(strip=True)
                            if title:
                                break
                
                # Extract company/employer
                company = ""
                company_elements = container.select(".artdeco-entity-lockup__caption")
                if company_elements:
                    company = company_elements[0].get_text(strip=True)
                
                if not company:
                    # Try other common company selectors
                    company_selectors = [
                        ".entity-result__secondary-subtitle",
                        ".search-result__info .subline-level-2"
                    ]
                    
                    for selector in company_selectors:
                        company_element = container.select_one(selector)
                        if company_element:
                            company = company_element.get_text(strip=True)
                            if company:
                                break
                
                # Skip if we don't have at least a name
                if not name:
                    continue
                    
                # Skip organizations by checking common patterns
                if self._is_organization_bs4(name, title, company, url):
                    print(f"BS4 skipping organization: {name}")
                    continue
                
                # Split name into first and last
                name_parts = name.split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                # Create profile
                profile = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "title": "",  # Empty title field that will be filled during profile visit
                    "description": title,  # Use the extracted title as description
                    "employer": company,
                    "linkedin_url": url,
                    "timestamp": datetime.now().isoformat()
                }
                
                profiles.append(profile)
                print(f"BS4 extracted profile {i}: {first_name} {last_name} - {title} - URL: {url}")
                
            except Exception as e:
                print(f"Error extracting profile with BeautifulSoup {i}: {e}")
        
        return profiles
    
    def _is_valid_linkedin_profile_url(self, url):
        """Check if a URL is a valid LinkedIn profile URL"""
        return url and ("/in/" in url or "linkedin.com/in/" in url or "miniProfileUrn" in url)
    
    def _normalize_linkedin_url(self, url):
        """Normalize LinkedIn URL to standard format"""
        # Remove query parameters
        if "?" in url:
            clean_url = url.split("?")[0]
        else:
            clean_url = url
        
        # Ensure we have an absolute URL
        if clean_url.startswith("/in/") or clean_url.startswith("in/"):
            # Convert relative URL to absolute
            return f"https://www.linkedin.com{clean_url if clean_url.startswith('/') else '/' + clean_url}"
        elif clean_url.startswith("https://") or clean_url.startswith("http://"):
            # Already an absolute URL
            return clean_url
        elif "linkedin.com" in clean_url:
            # Contains LinkedIn domain but might be missing protocol
            if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
                return f"https://{clean_url}"
            return clean_url
        elif "/in/" in clean_url:
            # Partial URL path
            return f"https://www.linkedin.com{clean_url if clean_url.startswith('/') else '/' + clean_url}"
        
        # If we can't normalize, return the original
        return url

    def _is_organization(self, name, title, container):
        """
        Determine if a profile is an organization rather than a person.
        
        Args:
            name (str): Name text extracted from profile
            title (str): Title or subtitle text
            container: The HTML container element
            
        Returns:
            bool: True if it's an organization, False if it's a person
        """
        # Organization indicator keywords
        org_keywords = [
            "university", "school", "college", "academy", "institute", 
            "department", "corporation", "inc", "llc", "ltd", "company",
            "organization", "organisation", "foundation", "association",
            "society", "group", "agency", "bureau", "office", "ministry",
            "committee", "council", "board", "authority", "commission",
            "global", "international", "national", "federal", "state", 
            "enterprise", "ventures", "partners", "industries", "solutions",
            "systems", "technologies", "services", "platform", "network"
        ]
        
        # Organization patterns in name
        if any(keyword in name.lower() for keyword in org_keywords):
            return True
            
        # Check for "Follow" button which often appears for organizations but not people
        follow_el = container.query_selector("button:has-text('Follow')")
        if follow_el:
            return True
            
        # Organizations often have "followers" count but not connection info
        followers_el = container.query_selector("*:has-text('followers')")
        connections_el = container.query_selector("*:has-text('connection')")
        if followers_el and not connections_el:
            return True
            
        # Check name patterns - real people typically have 2-3 words in name
        name_parts = name.split()
        if len(name_parts) > 4 or len(name_parts) == 1:
            # Organizations often have very long names or single word names
            return True
            
        # Check for lack of typical person attributes
        if not title or title.lower() in org_keywords:
            # Organizations often lack job titles or have org-like titles
            return True
            
        # Check URL pattern if available
        link_el = container.query_selector("a[href*='/company/']")
        if link_el:
            return True
            
        # Look for logo images which are common in org profiles
        logo_el = container.query_selector("img[alt*='logo']")
        if logo_el:
            return True
            
        return False

    def extract_employer_from_profile(self, profile_content):
        """
        Extract employer information from a LinkedIn profile page.
        First tries AI-powered extraction, then falls back to BeautifulSoup.
        
        Args:
            profile_content: HTML content of the profile page
            
        Returns:
            str: Extracted employer name or empty string if not found
        """
        print("Extracting employer information...")
        
        # Save the full profile HTML for debugging if needed
        try:
            with open("output/full_profile_html.txt", "w", encoding="utf-8") as f:
                f.write(profile_content)
            print("Saved profile HTML for debugging")
        except Exception as e:
            print(f"Error saving profile HTML: {e}")
        
        # First try AI-powered extraction
        try:
            print("Attempting AI-powered employer extraction...")
            ai_result = self.ai.analyze_single_profile(profile_content, save_to_file=False)
            if ai_result and ai_result.get("employer"):
                employer = ai_result.get("employer")
                print(f"AI extracted employer: {employer}")
                return employer
        except Exception as e:
            print(f"AI employer extraction failed: {e}")
        
        # Fall back to direct HTML parsing with BeautifulSoup
        try:
            print("Falling back to BeautifulSoup for employer extraction...")
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(profile_content, 'html.parser')
            
            # Try to find the current position section (first experience entry)
            # Look for the experience section first
            experience_section = soup.select_one("#experience")
            
            # Various selectors for employer information based on different LinkedIn layouts
            employer = None
            
            # Try to find the first experience entry with "Present" in the date
            experience_items = soup.select(".pvs-entity__sub-components li")
            for item in experience_items:
                date_text = item.text
                if "Present" in date_text:
                    # This might be a current position
                    employer_element = item.select_one("span.t-14.t-normal")
                    if employer_element:
                        text = employer_element.text.strip()
                        if "·" in text:
                            employer = text.split("·")[0].strip()
                            print(f"Found current employer from experience item: {employer}")
                            return employer
            
            # Try more specific selectors based on the provided HTML structure
            employer_elements = soup.select("span.t-14.t-normal")
            for element in employer_elements:
                text = element.text.strip()
                if "·" in text and ("Full-time" in text or "Part-time" in text):
                    employer = text.split("·")[0].strip()
                    print(f"Found employer from job type element: {employer}")
                    return employer
            
            # Try the most specific selector from the example
            first_experience = soup.select_one(".pvs-entity__sub-components li")
            if first_experience:
                company_element = first_experience.select_one("span.t-14.t-normal")
                if company_element and "·" in company_element.text:
                    employer = company_element.text.split("·")[0].strip()
                    print(f"Found employer from first experience: {employer}")
                    return employer
            
            # If still not found, try the fallback method from _extract_detailed_employer
            return self._extract_detailed_employer()
            
        except Exception as e:
            print(f"BeautifulSoup employer extraction failed: {e}")
        
        # If all methods fail, return empty string
        print("Could not extract employer information")
        return ""

    def extract_job_title_from_profile(self, profile_content):
        """
        Extract job title information from a LinkedIn profile page.
        First tries AI-powered extraction, then falls back to BeautifulSoup.
        
        Args:
            profile_content: HTML content of the profile page
            
        Returns:
            str: Extracted job title or empty string if not found
        """
        print("Extracting job title information...")
        
        # First try AI-powered extraction
        try:
            print("Attempting AI-powered job title extraction...")
            ai_result = self.ai.analyze_single_profile(profile_content, save_to_file=False)
            if ai_result and ai_result.get("job_title"):
                job_title = ai_result.get("job_title")
                print(f"AI extracted job title: {job_title}")
                return job_title
        except Exception as e:
            print(f"AI job title extraction failed: {e}")
        
        # Fall back to direct HTML parsing with BeautifulSoup
        try:
            print("Falling back to BeautifulSoup for job title extraction...")
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(profile_content, 'html.parser')
            
            # Try to find the current position title (first experience entry)
            # Look for the bold text in the first experience entry
            job_title = None
            
            # Try the most specific selector based on the provided HTML
            title_element = soup.select_one(".display-flex.align-items-center.mr1.t-bold span")
            if title_element:
                job_title = title_element.text.strip()
                if job_title:
                    print(f"Found job title from specific selector: {job_title}")
                    return job_title
            
            # Try to find the first experience entry with "Present" in the date
            experience_items = soup.select(".pvs-entity__sub-components li")
            for item in experience_items:
                date_text = item.text
                if "Present" in date_text:
                    # This might be a current position
                    title_element = item.select_one(".display-flex.align-items-center.mr1.t-bold span")
                    if title_element:
                        job_title = title_element.text.strip()
                        print(f"Found current job title from experience item: {job_title}")
                        return job_title
            
            # Try the headline as a fallback
            headline_element = soup.select_one(".text-body-medium")
            if headline_element:
                job_title = headline_element.text.strip()
                print(f"Using headline as job title fallback: {job_title}")
                return job_title
                
            # If still not found, try the fallback method
            return self._extract_detailed_job_title()
            
        except Exception as e:
            print(f"BeautifulSoup job title extraction failed: {e}")
        
        # If all methods fail, return empty string
        print("Could not extract job title information")
        return ""

    def _extract_detailed_job_title(self):
        """Extract detailed job title information from a profile page"""
        try:
            # Try different selectors for current position title
            title_selectors = [
                # Experience section - current position title
                "section.experience-section li:first-child .pv-entity__summary-info h3",
                # New LinkedIn layout
                "[data-field='experience_title']",
                # Alternative selector for experience
                ".pv-profile-section__list-item .pv-entity__summary-info h3",
                # More generic selector
                ".pv-position-entity .pv-entity__summary-info h3",
                # Very generic
                ".experience-section .pv-entity__summary-info h3"
            ]
            
            for selector in title_selectors:
                try:
                    title_el = self.browser.page.query_selector(selector)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if title:
                            return title
                except:
                    continue
            
            # Try to find the first experience entry as fallback
            experience_section = self.browser.page.query_selector("section#experience-section")
            if experience_section:
                first_entry = experience_section.query_selector("li.pv-entity__position-group-pager")
                if first_entry:
                    title_el = first_entry.query_selector(".pv-entity__summary-info h3")
                    if title_el:
                        return title_el.inner_text().strip()
            
            return ""
        except Exception as e:
            print(f"Error extracting detailed job title: {e}")
            return ""

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
            
            # Skip if this looks like an organization
            if self._is_organization(name, title, container):
                print(f"Skipping organization in container {index}: {name}")
                return {}
            
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
                                
                                # Skip if this looks like an organization
                                if self._is_organization(name, title, element):
                                    print(f"Skipping organization in fallback: {name}")
                                    continue
                                
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

    def _is_organization_bs4(self, name, title, company, url):
        """Improved detection of organizations in BeautifulSoup extraction"""
        # Check URL pattern - organizations don't have /in/ in their URLs
        if url and '/in/' not in url and 'linkedin.com/in/' not in url:
            return True
            
        # Check for organization indicators in the name
        org_indicators = [
            "University", "School", "College", "Academy", "Institute", 
            "Department", "Corporation", "Inc", "LLC", "Ltd", "Limited", "Company",
            "Organization", "Organisation", "Foundation", "Association",
            "Society", "Group", "Agency", "Bureau", "Office", "Ministry",
            "Committee", "Council", "Board", "Authority", "Commission",
            "Global", "International", "National", "Federal", "State", 
            "Enterprise", "Ventures", "Partners", "Industries", "Solutions",
            "Systems", "Technologies", "Services", "Platform", "Network",
            "freeCodeCamp", "Bootcamp", "E-learning"
        ]
        
        # Check if name contains organization indicators
        for indicator in org_indicators:
            if indicator.lower() in name.lower():
                return True
                
        # Check if name is too short (likely not a person)
        if len(name.split()) < 2:
            return True
            
        return False

    def _is_valid_profile(self, name, url=""):
        """Check if an extracted item is likely a valid person profile"""
        if not name:
            return False
            
        # Expanded list of organization keywords to filter out
        org_keywords = [
            "university", "school", "college", "online", "follow", "group", 
            "department", "subsidiary", "service", "learning", "followers",
            "academy", "institute", "corporation", "inc", "llc", "ltd", 
            "company", "organization", "organisation", "foundation", 
            "association", "society", "agency", "bureau", "office", 
            "ministry", "committee", "council", "board", "authority", 
            "commission", "global", "international", "national", "federal", 
            "enterprise", "ventures", "partners", "industries", "solutions",
            "systems", "technologies", "services", "platform", "network"
        ]
        
        # Check for organization keywords in the name
        if any(keyword.lower() in name.lower() for keyword in org_keywords):
            return False
            
        # Check for unusual name patterns (people typically have 2-3 name parts)
        name_parts = name.split()
        if len(name_parts) > 4 or len(name_parts) < 2:
            return False
            
        # Check URL pattern for LinkedIn profile
        if url:
            if "/company/" in url:
                return False
            if "/school/" in url:
                return False
            if not "/in/" in url and not "/pub/" in url:
                return False
                
        # Check for reasonable name length and structure
        if len(name.strip()) < 3 or len(name.split()) > 5:
            return False
            
        # Basic name pattern check (most names don't have special characters)
        if any(char in name for char in ["@", "&", "|", "/"]):
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
                                ".pv-entity__secondary-subtitle"
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
                            
                            # Skip if this looks like an organization
                            if self._is_organization(name, title, element):
                                print(f"Skipping organization in direct search: {name}")
                                continue
                                
                            # Only add if we found at least a name and it passes validation
                            if name and self._is_valid_profile(name, url):
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
                # Ensure all profiles have the correct structure
                for profile in data:
                    # If profile has 'title' but no 'description', copy title to description
                    if 'title' in profile and 'description' not in profile:
                        profile['description'] = profile['title']
                        profile['title'] = ""  # Reset title as it will be filled during profile visit
                existing_data.extend(data)
            else:
                # Handle single profile
                if 'title' in data and 'description' not in data:
                    data['description'] = data['title']
                    data['title'] = ""
                existing_data.append(data)
            
            # Write back to file with proper indentation for readability
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, indent=2, ensure_ascii=False)
                
            print(f"Data saved to JSON: {filename} ({len(existing_data)} total records)")
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")