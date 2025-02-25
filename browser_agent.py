from playwright.sync_api import sync_playwright
import time
import random
import config
from human_behavior import HumanBehavior

class BrowserAgent:
    def __init__(self, headless=False):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.human = HumanBehavior()
        
    def start(self):
        """Start the browser and create a new page"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']  # Help avoid detection
        )
        
        # Create context with specific user agent
        context = self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={'width': 1280, 'height': 800}
        )
        
        # Add additional browser configurations to make detection harder
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)
        
        self.page = context.new_page()
        
    def login(self, username, password):
        """Log in to LinkedIn"""
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
                return True
            else:
                print("Login may have failed. Current URL:", self.page.url)
                return False
        else:
            print("Already logged in or login page not available")
            return False
        
    def navigate_to(self, url):
        """Navigate to a LinkedIn page"""
        self.page.goto(url)
        self.human.delay(2, 4)
        
        # Random scrolling after loading a page (like a real user)
        if random.random() < config.SCROLL_PROBABILITY:
            self.human.scroll(self.page)
        
    def get_page_content(self):
        """Get the current page content"""
        return self.page.content()
    
    def take_screenshot(self, path="screenshot.png"):
        """Take a screenshot of the current page"""
        self.page.screenshot(path=path)
        return path
        
    def execute_action(self, action, selector=None, value=None):
        """Execute a browser action based on AI decision"""
        if action == "scroll":
            self.human.scroll(self.page)
            return True
        elif action == "click" and selector:
            return self.human.click(self.page, selector)
        elif action == "type" and selector and value:
            self.human.type_text(self.page, selector, value)
            return True
        elif action == "wait":
            self.human.delay(2, 5)
            return True
        else:
            print(f"Unknown action: {action}")
            return False
            
    def close(self):
        """Close the browser and stop playwright"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()