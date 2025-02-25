import config
import time
import os
import random
from browser_agent import BrowserAgent
from ai_controller import AIController
from data_extractor import DataExtractor
from human_behavior import HumanBehavior

def main():
    print("Starting LinkedIn AI Agent...")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Initialize components
    browser = BrowserAgent(headless=config.HEADLESS)
    browser.start()
    
    ai = AIController()
    extractor = DataExtractor(browser)
    
    # Track successful extractions
    successful_extractions = 0
    
    try:
        # Login to LinkedIn (if credentials are provided)
        if config.LINKEDIN_USERNAME and config.LINKEDIN_PASSWORD:
            print("Logging in to LinkedIn...")
            login_success = browser.login(config.LINKEDIN_USERNAME, config.LINKEDIN_PASSWORD)
            
            if not login_success:
                print("Login unsuccessful. Continuing without login...")
                # Take a screenshot to help debug
                browser.take_screenshot("output/login_failed.png")
        else:
            print("No credentials provided. Continuing without login...")
        
        # Process each target URL
        for url_index, url in enumerate(config.TARGET_URLS):
            print(f"\nProcessing URL {url_index + 1}/{len(config.TARGET_URLS)}: {url}")
            
            try:
                # Navigate to the profile
                browser.navigate_to(url)
                
                # Take a screenshot for reference
                screenshot_path = f"output/profile_{url_index + 1}.png"
                browser.take_screenshot(screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
                
                # Extract profile data
                profile_data = extractor.extract_profile_data(url)
                
                # Check if extraction was successful (at least got a name)
                if profile_data.get("name"):
                    print(f"Data extracted for: {profile_data['name']}")
                    
                    # Save the data
                    extractor.save_to_csv(profile_data, config.OUTPUT_CSV)
                    extractor.save_to_json(profile_data, config.OUTPUT_JSON)
                    
                    successful_extractions += 1
                else:
                    print("Data extraction failed for this profile")
                
                # Simulate human-like behavior between profiles
                time.sleep(random.uniform(3, 8))
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                # Continue with the next URL
                continue
        
        print(f"\nProcessing complete. Successfully extracted data from {successful_extractions}/{len(config.TARGET_URLS)} profiles.")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
    finally:
        # Always close the browser
        browser.close()
        print("LinkedIn AI Agent has completed its tasks")

if __name__ == "__main__":
    main()