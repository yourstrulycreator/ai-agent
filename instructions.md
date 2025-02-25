# LinkedIn AI Agent - Detailed Instructions

This document provides comprehensive instructions for building an AI agent that can navigate LinkedIn, extract profile data, and mimic human behavior while doing so.

## Project Overview

You're building an AI agent that can:
1. Autonomously navigate LinkedIn
2. Extract specific profile information
3. Behave like a human user to avoid detection
4. Use AI to adapt to different page layouts and make decisions

## Setup Instructions

### Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv linkedin_agent_env
   source linkedin_agent_env/bin/activate  # On Windows: linkedin_agent_env\Scripts\activate
   ```

2. Install required packages:
   ```bash
   pip install playwright langchain pydantic pandas pyautogui
   pip install torch transformers # For local AI model
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

### Project Structure

Create the following file structure:
```
linkedin_agent/
├── prompt.md
├── instructions.md
├── checklist.md
├── config.py           # Configuration parameters
├── browser_agent.py    # Browser automation code
├── ai_controller.py    # AI model integration
├── data_extractor.py   # LinkedIn data extraction
├── human_behavior.py   # Human-like behavior simulation
├── main.py             # Entry point for the application
└── requirements.txt    # Dependencies
```

## Implementation Details

### 1. Browser Automation (browser_agent.py)

Create a BrowserAgent class that:
- Initializes Playwright
- Handles LinkedIn login
- Navigates to specified pages
- Takes screenshots for the AI to analyze
- Executes actions based on AI decisions

Example implementation:
```python
from playwright.sync_api import sync_playwright
import time
import random
from human_behavior import HumanBehavior

class BrowserAgent:
    def __init__(self, headless=False):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.human = HumanBehavior()
        
    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        
    def login(self, username, password):
        self.page.goto('https://www.linkedin.com/login')
        self.human.delay()
        
        # Fill in login details
        self.page.fill('#username', username)
        self.human.delay()
        self.page.fill('#password', password)
        self.human.delay()
        
        # Click sign in
        self.page.click('button[type="submit"]')
        self.human.delay(3, 5)  # Longer delay for login
        
    def navigate_to(self, url):
        self.page.goto(url)
        self.human.delay(2, 4)
        
    def get_page_content(self):
        return self.page.content()
    
    def take_screenshot(self):
        return self.page.screenshot()
        
    def execute_action(self, action, selector=None):
        if action == "scroll":
            self.human.scroll(self.page)
        elif action == "click" and selector:
            self.human.click(self.page, selector)
        # Add more actions as needed
            
    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
```

### 2. AI Controller (ai_controller.py)

Create an AIController class that:
- Loads a language model (local or via API)
- Processes page content
- Decides on next actions
- Identifies elements to extract

Example implementation:
```python
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline

class AIController:
    def __init__(self):
        # Initialize a local model using HuggingFace
        local_pipeline = pipeline(
            "text-generation",
            model="distilgpt2",  # Use a lightweight model or replace with your preferred model
            max_length=100
        )
        
        self.llm = HuggingFacePipeline(pipeline=local_pipeline)
        
        # Create a prompt template for decision making
        self.decision_prompt = PromptTemplate(
            input_variables=["page_content", "current_state"],
            template="""
            You are an AI agent browsing LinkedIn. Given the current page content and state,
            decide what action to take next.
            
            Current page content: {page_content}
            Current state: {current_state}
            
            Possible actions:
            1. scroll
            2. click [selector]
            3. extract [data_type]
            
            Your decision (just return the action):
            """
        )
        
        self.decision_chain = LLMChain(llm=self.llm, prompt=self.decision_prompt)
        
    def decide_next_action(self, page_content, current_state):
        decision = self.decision_chain.run(
            page_content=page_content[:1000],  # Truncate to avoid token limits
            current_state=current_state
        )
        
        return decision.strip()
    
    def identify_elements(self, page_content, data_type):
        # Create a specialized prompt for element identification
        element_prompt = PromptTemplate(
            input_variables=["page_content", "data_type"],
            template="""
            Analyze this LinkedIn page content and identify the CSS selector
            that would target the {data_type} element.
            
            Page content: {page_content}
            
            CSS selector for {data_type}:
            """
        )
        
        element_chain = LLMChain(llm=self.llm, prompt=element_prompt)
        selector = element_chain.run(
            page_content=page_content[:1000],
            data_type=data_type
        )
        
        return selector.strip()
```

### 3. Data Extractor (data_extractor.py)

Create a DataExtractor class that:
- Uses selectors to extract specific data from the page
- Cleans and structures the extracted data
- Saves data to CSV or JSON

Example implementation:
```python
import csv
import json
from datetime import datetime

class DataExtractor:
    def __init__(self, browser_agent):
        self.browser = browser_agent
        
    def extract_profile_data(self, profile_url):
        self.browser.navigate_to(profile_url)
        
        # Extract basic profile information using page selectors
        # These selectors need to be updated based on LinkedIn's current layout
        data = {
            "name": self._extract_text("h1.text-heading-xlarge"),
            "title": self._extract_text("div.text-body-medium"),
            "company": self._extract_text("span.text-body-small:nth-child(1)"),
            "location": self._extract_text("span.text-body-small:nth-child(2)"),
            "url": profile_url,
            "timestamp": datetime.now().isoformat()
        }
        
        return data
    
    def _extract_text(self, selector):
        try:
            element = self.browser.page.query_selector(selector)
            if element:
                return element.inner_text()
            return ""
        except Exception as e:
            print(f"Error extracting {selector}: {e}")
            return ""
    
    def save_to_csv(self, data, filename):
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            
            # Write header if file is empty
            if file.tell() == 0:
                writer.writeheader()
                
            writer.writerow(data)
    
    def save_to_json(self, data, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
            
        existing_data.append(data)
        
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=2, ensure_ascii=False)
```

### 4. Human Behavior Simulation (human_behavior.py)

Create a HumanBehavior class that:
- Adds randomized delays between actions
- Implements realistic mouse movements
- Creates human-like scrolling patterns

Example implementation:
```python
import time
import random
import math

class HumanBehavior:
    def delay(self, min_seconds=0.5, max_seconds=2.5):
        """Add a random delay between actions"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def move_mouse(self, page, x, y, steps=10):
        """Move mouse in a human-like curve rather than straight line"""
        # Get current position
        current_pos = page.mouse.position
        start_x, start_y = current_pos["x"], current_pos["y"]
        
        # Create a curved path
        for i in range(steps + 1):
            progress = i / steps
            # Add some randomness to the path
            noise_x = random.gauss(0, 2)
            noise_y = random.gauss(0, 2)
            
            # Calculate position along a curved path
            cx = start_x + (x - start_x) * (3 * (progress ** 2) - 2 * (progress ** 3))
            cy = start_y + (y - start_y) * (3 * (progress ** 2) - 2 * (progress ** 3))
            
            # Add the noise
            cx += noise_x
            cy += noise_y
            
            # Move to this position
            page.mouse.move(cx, cy)
            
            # Small delay between movements
            time.sleep(random.uniform(0.01, 0.03))
            
    def click(self, page, selector):
        """Click on an element with human-like behavior"""
        element = page.query_selector(selector)
        if element:
            # Get element position
            bbox = element.bounding_box()
            if bbox:
                # Calculate a random position within the element
                x = bbox["x"] + random.uniform(5, bbox["width"] - 5)
                y = bbox["y"] + random.uniform(5, bbox["height"] - 5)
                
                # Move to element
                self.move_mouse(page, x, y)
                self.delay(0.1, 0.3)
                
                # Click
                page.mouse.click(x, y)
                return True
        return False
    
    def scroll(self, page, distance=None):
        """Perform human-like scrolling"""
        if distance is None:
            # Random scroll distance
            distance = random.randint(100, 500)
        
        # Break the scroll into multiple smaller scrolls
        scroll_steps = random.randint(3, 8)
        for _ in range(scroll_steps):
            step_distance = distance / scroll_steps
            # Add some randomness to each step
            step_distance += random.uniform(-10, 10)
            
            page.mouse.wheel(0, step_distance)
            self.delay(0.1, 0.4)
```

### 5. Configuration (config.py)

Create a configuration file:
```python
# LinkedIn credentials
LINKEDIN_USERNAME = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# AI model settings
MODEL_NAME = "distilgpt2"  # or your preferred model

# Browser settings
HEADLESS = False  # Set to True for production
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Output settings
OUTPUT_CSV = "linkedin_data.csv"
OUTPUT_JSON = "linkedin_data.json"

# Human behavior settings
MIN_DELAY = 1.0  # Minimum delay between actions in seconds
MAX_DELAY = 3.0  # Maximum delay between actions in seconds
SCROLL_PROBABILITY = 0.7  # Probability of scrolling on a page

# URLs to process
TARGET_URLS = [
    "https://www.linkedin.com/in/example-profile-1/",
    "https://www.linkedin.com/in/example-profile-2/",
    # Add more URLs as needed
]
```

### 6. Main Application (main.py)

Create the entry point:
```python
import config
from browser_agent import BrowserAgent
from ai_controller import AIController
from data_extractor import DataExtractor
from human_behavior import HumanBehavior

def main():
    # Initialize components
    browser = BrowserAgent(headless=config.HEADLESS)
    browser.start()
    
    ai = AIController()
    extractor = DataExtractor(browser)
    
    try:
        # Login to LinkedIn
        browser.login(config.LINKEDIN_USERNAME, config.LINKEDIN_PASSWORD)
        
        # Process each target URL
        for url in config.TARGET_URLS:
            print(f"Processing: {url}")
            
            # Navigate to the profile
            browser.navigate_to(url)
            
            # Extract profile data
            profile_data = extractor.extract_profile_data(url)
            
            # Save the data
            extractor.save_to_csv(profile_data, config.OUTPUT_CSV)
            extractor.save_to_json(profile_data, config.OUTPUT_JSON)
            
            print(f"Data extracted for: {profile_data['name']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always close the browser
        browser.close()

if __name__ == "__main__":
    main()
```

## Running the Application

1. Make sure your LinkedIn credentials are set in config.py
2. Run the application:
   ```bash
   python main.py
   ```
3. The agent will start, log in to LinkedIn, and process the target URLs
4. Extracted data will be saved in the specified CSV and JSON files
