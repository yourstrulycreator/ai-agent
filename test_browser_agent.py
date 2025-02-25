import config
from browser_agent import BrowserAgent
import time

def test_browser_agent():
    print("Testing browser agent...")
    
    # Initialize browser agent
    browser = BrowserAgent(headless=False)
    browser.start()
    
    try:
        # Test navigation (to a public page that doesn't require login)
        print("Testing navigation to LinkedIn public page...")
        browser.navigate_to("https://www.linkedin.com/company/microsoft/")
        print("Navigation successful")
        
        # Take a screenshot
        screenshot_path = browser.take_screenshot("test_screenshot.png")
        print(f"Screenshot saved to {screenshot_path}")
        
        # Test scrolling action
        print("Testing scroll action...")
        browser.execute_action("scroll")
        print("Scroll action completed")
        
        # Wait to observe
        time.sleep(2)
        
        # Uncomment to test login (update config.py with your credentials first)
        # print("Testing LinkedIn login...")
        # login_success = browser.login(config.LINKEDIN_USERNAME, config.LINKEDIN_PASSWORD)
        # print(f"Login success: {login_success}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Close the browser
        browser.close()
        print("Browser agent test completed")

if __name__ == "__main__":
    test_browser_agent()