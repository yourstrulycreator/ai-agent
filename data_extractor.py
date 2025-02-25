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
        """Save extracted data to a CSV file"""
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            
            # Write header if file is empty or doesn't exist
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(data)
            print(f"Data saved to CSV: {filename}")
    
    def save_to_json(self, data, filename):
        """Save extracted data to a JSON file"""
        try:
            # Load existing data if file exists
            if os.path.isfile(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    try:
                        existing_data = json.load(file)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []
                
            # Append new data
            if isinstance(existing_data, list):
                existing_data.append(data)
            else:
                existing_data = [existing_data, data]
            
            # Write back to file
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, indent=2, ensure_ascii=False)
                
            print(f"Data saved to JSON: {filename}")
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")