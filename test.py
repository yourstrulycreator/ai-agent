import os
import config
import json

def test_ai_controller():
    """Test the AI controller in isolation"""
    print("\n== Testing AI Controller ==")
    
    try:
        from ai_controller import AIController
        
        # Initialize AI controller
        print("Initializing AI controller...")
        ai = AIController()
        
        # Test decision making with sample content
        sample_content = """
        <div class="profile-info">
            <h1 class="text-heading-xlarge">John Smith</h1>
            <div class="text-body-medium">Software Engineer at Tech Company</div>
            <span class="text-body-small">San Francisco Bay Area</span>
        </div>
        <section class="experience">
            <h2>Experience</h2>
            <h3>Software Engineer</h3>
            <p>Tech Company</p>
        </section>
        """
        
        print("\nTesting decision making...")
        decision = ai.decide_next_action(sample_content, "viewing profile")
        print(f"AI decision: {decision}")
        
        print("\nTesting element identification...")
        selector = ai.identify_elements(sample_content, "name")
        print(f"Selector for 'name': {selector}")
        
        print("\nAI Controller test completed successfully")
        return True
        
    except Exception as e:
        print(f"AI Controller test failed: {e}")
        return False

def test_browser_agent():
    """Test the browser agent in headless mode"""
    print("\n== Testing Browser Agent ==")
    
    try:
        from browser_agent import BrowserAgent
        
        # Initialize browser in headless mode for testing
        print("Initializing browser...")
        browser = BrowserAgent(headless=True)
        browser.start()
        
        try:
            # Test navigation to a public page
            print("\nTesting navigation...")
            success = browser.navigate_to("https://www.linkedin.com/")
            print(f"Navigation successful: {success}")
            
            # Take a screenshot to verify
            screenshot_path = "test_screenshot.png"
            browser.take_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            print("\nBrowser Agent test completed successfully")
            return True
            
        finally:
            # Always close the browser
            browser.close()
            
    except Exception as e:
        print(f"Browser Agent test failed: {e}")
        return False

def test_data_extraction(url=None):
    """Test data extraction from a LinkedIn page"""
    print("\n== Testing People Data Extraction ==")
    
    if not url:
        print("No URL provided for testing. Skipping school people extraction test.")
        return False
    
    try:
        from browser_agent import BrowserAgent
        from data_extractor import DataExtractor
        
        # Initialize components
        print("Initializing components...")
        browser = BrowserAgent(headless=False)  # Use non-headless for data extraction
        browser.start()
        extractor = DataExtractor(browser)
        
        try:
            # Login if credentials provided
            if config.LINKEDIN_USERNAME and config.LINKEDIN_PASSWORD:
                print("\nLogging in...")
                login_success = browser.login(config.LINKEDIN_USERNAME, config.LINKEDIN_PASSWORD)
                print(f"Login successful: {login_success}")
            
            # Extract data from the school people page
            print(f"\nExtracting data from: {url}")
            people_data = extractor.extract_people_data(url)
            
            # Display extracted data
            print("\nExtracted people data:")
            for profile in people_data:
                print(f"  Name: {profile['first_name']} {profile['last_name']}, Title: {profile['title']}, Employer: {profile['employer']}")
            
            # Save to test files
            test_csv = "test__data.csv"
            test_json = "test_data.json"
            extractor.save_to_csv(people_data, test_csv)
            extractor.save_to_json(people_data, test_json)
            print(f"\nData saved to {test_csv} and {test_json}")
            
            print("\nPeople Data Extraction test completed successfully")
            return True
            
        finally:
            # Always close the browser
            browser.close()
            
    except Exception as e:
        print(f"People Data Extraction test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== LinkedIn AI Agent Test Suite ===")
    
    # Create output directories
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Run tests
    ai_test = test_ai_controller()
    browser_test = test_browser_agent()
    
    # Ask for data extraction test
    run_extraction = input("\nRun data extraction test? (y/n): ").lower() == 'y'
    extraction_test = test_data_extraction() if run_extraction else "Skipped"
    
    # Print summary
    print("\n=== Test Results ===")
    print(f"AI Controller: {'PASSED' if ai_test else 'FAILED'}")
    print(f"Browser Agent: {'PASSED' if browser_test else 'FAILED'}")
    print(f"Data Extraction: {'PASSED' if extraction_test == True else ('FAILED' if extraction_test == False else extraction_test)}")
    
    if ai_test and browser_test and (extraction_test == True or extraction_test == "Skipped"):
        print("\nAll tests passed! Your LinkedIn AI Agent is ready to use.")
        print("Run the main.py script to start the agent with your configured settings.")
    else:
        print("\nSome tests failed. Please review the errors above before proceeding.")

if __name__ == "__main__":
    main()