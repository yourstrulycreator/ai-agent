from playwright.sync_api import sync_playwright
import time
import random
import config
from human_behavior import HumanBehavior
import os
import json

class BrowserAgent:
    def __init__(self, headless=False):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.human = HumanBehavior()
        self.session_file = "session_data.json"
        self.rate_limit_delay = (5, 15)  # Delay range when rate limiting suspected
        
    def start(self):
        """Start the browser and create a new page"""
        self.playwright = sync_playwright().start()
        
        # Start with more anti-detection features
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        )
        
        # Create context with more realistic profile
        context = self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={'width': 1280, 'height': 800},
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            has_touch=False
        )
        
        # Add additional browser configurations to make detection harder
        context.add_init_script("""
            // Overwrite the automation flags
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Overwrite the plugins
            const originalPlugins = navigator.plugins;
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        self.page = context.new_page()
        
        # Load session cookies if available
        self._load_session()
        
    def _save_session(self):
        """Save session cookies for future use"""
        if self.page:
            try:
                cookies = self.page.context.cookies()
                os.makedirs("data", exist_ok=True)
                with open(os.path.join("data", self.session_file), 'w') as f:
                    json.dump(cookies, f)
                print("Session saved successfully")
            except Exception as e:
                print(f"Error saving session: {e}")
    
    def _load_session(self):
        """Load session cookies if available"""
        session_path = os.path.join("data", self.session_file)
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r') as f:
                    cookies = json.load(f)
                self.page.context.add_cookies(cookies)
                print("Session loaded successfully")
                return True
            except Exception as e:
                print(f"Error loading session: {e}")
        return False
        
    def login(self, username, password, max_retries=3):
        """Log in to LinkedIn with improved error handling and retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"Login attempt {attempt+1}/{max_retries}")
                
                # First check if we're already logged in by visiting the feed page
                self.page.goto('https://www.linkedin.com/feed/', timeout=60000)
                self.human.delay()
                
                # If we're already on the feed, we're logged in
                if self.page.url.startswith('https://www.linkedin.com/feed'):
                    print("Already logged in")
                    return True
                    
                # Otherwise, go to login page
                self.page.goto('https://www.linkedin.com/login', timeout=60000)
                self.human.delay(2, 4)  # Longer delay to ensure page loads
                
                # Take screenshot for debugging
                self.take_screenshot(f"login_page_attempt_{attempt+1}.png")
                
                # Check if we're on the login page
                username_selector = '#username'
                password_selector = '#password'
                submit_selector = 'button[type="submit"]'
                
                # Wait for selectors to be visible
                print("Waiting for login form elements...")
                self.page.wait_for_selector(username_selector, timeout=10000)
                
                # Clear fields first (in case there's text already)
                self.page.fill(username_selector, "")
                self.human.delay(0.5, 1)
                self.page.fill(password_selector, "")
                self.human.delay(0.5, 1)
                
                # Fill in login details with human-like behavior
                print(f"Entering username: {username}")
                self.human.type_text(self.page, username_selector, username)
                self.human.delay(1, 2)
                
                print(f"Entering password")
                self.human.type_text(self.page, password_selector, password)
                self.human.delay(1, 2)
                
                # Check if fields are filled properly
                entered_username = self.page.input_value(username_selector)
                if not entered_username:
                    print("Username field appears to be empty. Retrying...")
                    continue
                    
                # Click sign in
                print("Clicking sign in button")
                self.human.click(self.page, submit_selector)
                
                # Wait longer for login to complete
                self.human.delay(5, 8)
                
                # Take another screenshot to see where we are
                self.take_screenshot(f"after_login_attempt_{attempt+1}.png")
                
                # Check if login was successful
                if self.page.url.startswith('https://www.linkedin.com/feed'):
                    print("Login successful")
                    # Save session for future use
                    self._save_session()
                    return True
                
                # Check for different error scenarios
                if "error" in self.page.url.lower() or "challenge" in self.page.url.lower():
                    print(f"Login error detected. Current URL: {self.page.url}")
                    
                # Check for empty fields error
                error_text = self.page.text_content('.alert.error') or ""
                if "enter an email" in error_text.lower() or "enter a password" in error_text.lower():
                    print(f"Empty field error detected: {error_text}")
                    continue  # Retry login
                    
                # Check for incorrect credentials
                if "that's not the right password" in self.page.content().lower():
                    print("Incorrect password detected")
                    return False  # Don't retry with same wrong credentials
                    
                # Check for captcha or security verification
                if "checkpoint" in self.page.url or self.page.query_selector('input[name="pin"]'):
                    print("Security verification required. Please complete the captcha.")
                    return False  # Can't proceed without user intervention
                
            except Exception as e:
                print(f"An error occurred during login attempt: {e}")
                continue  # Retry on error
                
        print("Max login attempts reached. Please check your credentials or account status.")
        return False  # Failed to log in after max retries
        
    def navigate_to(self, url, max_retries=3):
        """Navigate to a LinkedIn page with retry logic"""
        for attempt in range(max_retries):
            try:
                self.page.goto(url, timeout=60000)  # 30 second timeout
                self.human.delay(2, 4)
                
                # Check for rate limiting or security challenges
                if self._check_for_blocks():
                    if attempt < max_retries - 1:
                        # Wait longer between retries
                        wait_time = random.uniform(*self.rate_limit_delay) * (attempt + 1)
                        print(f"Detected possible rate limiting, waiting {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("Maximum retries reached. Could not access page.")
                        return False
                
                # Random scrolling after loading a page (like a real user)
                if random.random() < config.SCROLL_PROBABILITY:
                    self.human.scroll(self.page)
                
                return True
                
            except Exception as e:
                print(f"Navigation error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(5, 15)
                    print(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
        
        return False
    
    def _check_for_blocks(self):
        """Check if LinkedIn is showing blocking/captcha pages"""
        # Check for common blocking indicators
        page_content = self.page.content().lower()
        if any(term in page_content for term in [
            "unusual activity", 
            "security verification",
            "prove you're a human",
            "captcha",
            "automated access",
            "too many requests"
        ]):
            return True
            
        # Check for challenge URLs
        if any(term in self.page.url for term in [
            "checkpoint",
            "challenge",
            "captcha"
        ]):
            return True
            
        return False
        
    def get_page_content(self):
        """Get the current page content"""
        return self.page.content()
    
    def take_screenshot(self, path="screenshot.png"):
        """Take a screenshot of the current page"""
        # Make sure the directory exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        self.page.screenshot(path=path)
        return path
        
    def execute_action(self, action, selector=None, value=None):
        """Execute a browser action based on AI decision"""
        if action == "scroll":
            self.human.scroll(self.page)
            return True
        elif action == "click" and selector:
            success = self.human.click(self.page, selector)
            if not success:
                print(f"Could not find element to click: {selector}")
            return success
        elif action == "type" and selector and value:
            success = self.human.type_text(self.page, selector, value)
            if not success:
                print(f"Could not find element to type into: {selector}")
            return success
        elif action == "wait":
            self.human.delay(2, 5)
            return True
        else:
            print(f"Unknown action: {action}")
            return False
            
    def close(self):
        """Close the browser and stop playwright"""
        # Save session before closing
        self._save_session()
        
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def find_and_scroll_to_profile(self, profile_name):
    """Find a profile by name and scroll to it with visible cursor movement"""
    try:
        # Try different selectors that might contain the profile name
        selectors = [
            ".entity-result__title-text",
            ".search-result__info .actor-name",
            ".org-people-profile-card__profile-title",
            ".artdeco-entity-lockup__title"
        ]
        
        found_element = None
        
        # Try each selector
        for selector in selectors:
            elements = self.page.query_selector_all(selector)
            for element in elements:
                text = element.inner_text().strip()
                if profile_name.lower() in text.lower():
                    found_element = element
                    break
            if found_element:
                break
        
        if found_element:
            # Get element position
            bbox = found_element.bounding_box()
            if bbox:
                # Calculate center of element
                x = bbox["x"] + bbox["width"] / 2
                y = bbox["y"] + bbox["height"] / 2
                
                # First scroll element into view with a smooth scroll
                self.page.evaluate("""(y) => {
                    window.scrollTo({
                        top: y - (window.innerHeight / 2),
                        behavior: 'smooth'
                    });
                }""", y)
                
                # Wait for scroll to complete
                self.human.delay(1, 2)
                
                # Then move cursor to the element with visible movement
                self.human.move_mouse(self.page, x, y, steps=25)  # Increased steps for more visible movement
                
                # Optional: Highlight with a brief hover
                self.human.delay(0.5, 1)
                
                return True
        
        print(f"Could not find element for profile: {profile_name}")
        return False
        
    except Exception as e:
        print(f"Error scrolling to profile: {e}")
        return False