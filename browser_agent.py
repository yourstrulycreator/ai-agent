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
        
    def login(self, username, password):
        """Log in to LinkedIn"""
        # First check if we're already logged in by visiting the feed page
        self.page.goto('https://www.linkedin.com/feed/')
        self.human.delay()
        
        # If we're already on the feed, we're logged in
        if self.page.url.startswith('https://www.linkedin.com/feed'):
            print("Already logged in")
            return True
            
        # Otherwise, go to login page
        self.page.goto('https://www.linkedin.com/login')
        self.human.delay()
        
        # Check if we're on the login page
        if self.page.query_selector('#username'):
            # Fill in login details
            self.human.type_text(self.page, '#username', username)
            self.human.delay()
            self.human.type_text(self.page, '#password', password)
            self.human.delay()
            
            # Click sign in
            self.human.click(self.page, 'button[type="submit"]')
            self.human.delay(3, 5)  # Longer delay for login
            
            # Check if login was successful
            if self.page.url.startswith('https://www.linkedin.com/feed'):
                print("Login successful")
                # Save session for future use
                self._save_session()
                return True
            else:
                print("Login may have failed. Current URL:", self.page.url)
                
                # Check for captcha or security verification
                if "checkpoint" in self.page.url or self.page.query_selector('input[name="pin"]'):
                    print("SECURITY VERIFICATION REQUIRED: Please complete it manually")
                    # Give time for manual verification (2 minutes)
                    self.human.delay(120, 120)
                    
                    # Check if verification was successful
                    if self.page.url.startswith('https://www.linkedin.com/feed'):
                        print("Verification successful")
                        self._save_session()
                        return True
                
                return False
        else:
            print("Already logged in or login page not available")
            return False
        
    def navigate_to(self, url, max_retries=3):
        """Navigate to a LinkedIn page with retry logic"""
        for attempt in range(max_retries):
            try:
                self.page.goto(url, timeout=30000)  # 30 second timeout
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