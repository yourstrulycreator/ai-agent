import config
import time
import os
import random
from browser_agent import BrowserAgent
from ai_controller import AIController
from data_extractor import DataExtractor
from human_behavior import HumanBehavior
from screen_recorder import ScreenRecorder

def main():
    print("Starting LinkedIn AI Agent...")
    
    # Create output and data directories if they don't exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Initialize screen recorder
    recorder = ScreenRecorder()
    recording_active = True
    
    try:
        # Start screen recording if requested
        if config.RECORD_SCREEN:
            recording_active = recorder.start()
            print("Screen recording started")
    
        # Initialize components
        browser = BrowserAgent(headless=config.HEADLESS)
        browser.start()
        
        # Increase page load timeout
        browser.page.set_default_timeout(120000)  # Increase to 120 seconds
        browser.page.set_default_navigation_timeout(120000)
        
        # Add initial delay to ensure browser is fully started
        time.sleep(5)
        
        ai = AIController()
        extractor = DataExtractor(browser)
        human = HumanBehavior()
    
    except Exception as e:
        print(f"Error during initialization: {e}")
        if recording_active:
            recorder.stop()
        if 'browser' in locals() and browser:
            browser.close()
        return
    
    # Track successful extractions
    successful_extractions = 0
    last_frame_time = time.time()
    
    try:
        # Login to LinkedIn (if credentials are provided)
        if config.LINKEDIN_USERNAME and config.LINKEDIN_PASSWORD:
            print("Logging in to LinkedIn...")
            try:
                # Add delay before login attempt
                time.sleep(3)
                
                # Capture frame before login attempt
                if recording_active:
                    recorder.capture_frame()
                
                login_success = browser.login(config.LINKEDIN_USERNAME, config.LINKEDIN_PASSWORD)
                
                # Capture frame after login attempt
                if recording_active:
                    recorder.capture_frame()
                
                if not login_success:
                    print("Login unsuccessful. Continuing without login...")
                    try:
                        browser.take_screenshot("output/login_failed.png")
                    except Exception as e:
                        print(f"Failed to take login failure screenshot: {e}")
                    browser.close()
                    if recording_active:
                        recorder.stop()
                    return
            except Exception as e:
                print(f"Login process failed: {e}")
                browser.close()
                if recording_active:
                    recorder.stop()
                return
            
            if not login_success:
                print("Login unsuccessful. Continuing without login...")
                browser.take_screenshot("output/login_failed.png")
                if recording_active:
                    recorder.stop()
                return  # Exit if login fails
        else:
            print("No credentials provided. Continuing without login...")
            if recording_active:
                recorder.stop()
            return  # Exit if no credentials
        
        # Process each target URL
        for url_index, url in enumerate(config.TARGET_URLS):
            print(f"\nProcessing URL {url_index + 1}/{len(config.TARGET_URLS)}: {url}")
            
            try:
                # Navigate to the profile with human-like behavior
                browser.navigate_to(url)
                human.delay(2, 4)  # Random delay before actions
                
                # Capture frame after navigation
                if recording_active:
                    recorder.capture_frame()
                
                # Take a screenshot for reference
                #try:
                    #screenshot_path = f"output/profile_{url_index + 1}.png"
                    #browser.take_screenshot(screenshot_path)
                    #print(f"Screenshot saved to {screenshot_path}")
                #except Exception as e:
                #    print(f"Failed to take screenshot: {e}")
                    # Continue execution even if screenshot fails
                
                # Simulate human scrolling
                human.scroll(browser.page)
                human.delay(1, 2)
                
                # Capture frame after scrolling
                if recording_active:
                    recorder.capture_frame()
                
                # Extract profile data
                people_data = extractor.extract_people_data(url)
                
                # Make sure people_data is not None before processing
                if people_data:
                    print(f"Found {len(people_data)} profiles to process")
                    
                    # Process and validate extracted profiles
                    valid_profiles = []
                    for profile_index, profile in enumerate(people_data):
                        # Skip LinkedIn Member profiles (usually private)
                        if profile.get('first_name') == 'LinkedIn' and profile.get('last_name') == 'Member':
                            continue
                            
                        # Validate individual profiles
                        if profile.get('first_name') and profile.get('last_name'):
                            valid_profiles.append(profile)
                            print(f"Data extracted for: {profile['first_name']} {profile['last_name']}")
                            
                            # Visit the profile if URL is available
                            if profile.get('linkedin_url'):
                                try:
                                    print(f"Visiting profile: {profile['linkedin_url']}")
                                    
                                    # Navigate to the profile
                                    browser.navigate_to(profile['linkedin_url'])
                                    
                                    # Capture frame after profile navigation
                                    if recording_active:
                                        recorder.capture_frame()
                                    
                                    # Simulate human-like behavior while viewing the profile
                                    human.delay(1, 2)  # Initial pause to look at the page
                                    
                                    # Take a screenshot of the profile
                                    #profile_screenshot = f"output/profile_{profile['first_name']}_{profile['last_name']}.png"
                                    #browser.take_screenshot(profile_screenshot)
                                    
                                    # Scroll down slowly to view the profile
                                    for _ in range(3):  # Scroll a few times
                                        human.scroll(browser.page, smooth=True)
                                        human.delay(1, 2)  # Pause between scrolls
                                        
                                        # Capture frame during scrolling (not every scroll to avoid too many frames)
                                        if recording_active and time.time() - last_frame_time > 2:
                                            recorder.capture_frame()
                                            last_frame_time = time.time()

                                    # Add extra wait time before extraction to ensure all content is loaded
                                    browser.page.wait_for_timeout(5000)  # Increased to 5 seconds
                                    
                                    # Capture frame before extraction
                                    if recording_active:
                                        recorder.capture_frame()
                                    
                                    # Extract employer information from the profile page
                                    profile_content = browser.get_page_content()
                                    
                                    # Extract both employer and job title information
                                    employer_info = extractor.extract_employer_from_profile(profile_content)
                                    job_title = extractor.extract_job_title_from_profile(profile_content)
                                    
                                    if employer_info:
                                        profile['employer'] = employer_info
                                        print(f"Extracted employer: {employer_info}")
                                    
                                    if job_title:
                                        profile['title'] = job_title
                                        print(f"Extracted job title: {job_title}")
                                    
                                    # Navigate back to the search results
                                    browser.navigate_to(url)
                                    human.delay(2, 3)  # Wait for page to load
                                    
                                    # NEW CODE: Scroll to the position of the next profile if available
                                    if profile_index < len(people_data) - 1:
                                        # Try to find the next profile's element to scroll to
                                        next_profile_name = f"{people_data[profile_index + 1].get('first_name', '')} {people_data[profile_index + 1].get('last_name', '')}".strip()
                                        if next_profile_name:
                                            print(f"Scrolling to next profile: {next_profile_name}")
                                            
                                            # First, perform a general scroll to approximate position
                                            scroll_amount = (profile_index + 1) * 300  # Rough estimate of profile card height
                                            human.scroll(browser.page, distance=scroll_amount, smooth=True)
                                            human.delay(1, 2)
                                            
                                            # Then try to find and scroll to the specific element
                                            # This uses a more visible cursor movement to the next profile
                                            browser.find_and_scroll_to_profile(next_profile_name)
                                    
                                    # Capture frame after returning to search results
                                    if recording_active:
                                        recorder.capture_frame()
                                    
                                except Exception as e:
                                    print(f"Error visiting profile: {e}")
                            
                            # Save individual profiles - IMPORTANT: Save even if URL visit fails
                            extractor.save_to_csv([profile], config.OUTPUT_CSV)
                            extractor.save_to_json([profile], config.OUTPUT_JSON)
                            
                            successful_extractions += 1
                    
                    print(f"Successfully extracted {successful_extractions} profiles")
                else:
                    print("No profiles were extracted")
                
                # Simulate human-like behavior between profiles
                human.delay(3, 8)
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                # Capture frame when error occurs
                if recording_active:
                    recorder.capture_frame()
                continue
    
        print(f"\nProcessing complete. Successfully extracted {successful_extractions} profiles.")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
    finally:
        try:
            # Stop screen recording if active
            if recording_active:
                recorder.stop()
                print("Screen recording stopped")
                
            # Always close the browser
            if browser and browser.page:
                browser.close()
        except Exception as e:
            print(f"Warning: Error while closing browser: {e}")
        print("LinkedIn AI Agent has completed its tasks")

if __name__ == "__main__":
    main()