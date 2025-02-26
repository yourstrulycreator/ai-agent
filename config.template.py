# LinkedIn credentials
LINKEDIN_USERNAME = "your_email@example.com"
LINKEDIN_PASSWORD = "your_password"

# AI model settings
MODEL_NAME = "distilgpt2"

# Browser settings
HEADLESS = False
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Output settings
OUTPUT_CSV = "linkedin_data.csv"
OUTPUT_JSON = "linkedin_data.json"

# Human behavior settings
MIN_DELAY = 1.0
MAX_DELAY = 3.0
SCROLL_PROBABILITY = 0.7

# URLs to process
TARGET_URLS = [
    "https://www.linkedin.com/school/stanford-university/people/?keywords=angel%20investor",
    # Add more URLs as needed
]