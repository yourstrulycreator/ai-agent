# LinkedIn credentials
LINKEDIN_USERNAME = "mike.nwankwo@outlook.com"
LINKEDIN_PASSWORD = "justrocks"

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
    "https://www.linkedin.com/school/stanford-university/people/?keywords=angel%20investor",
    # Add more URLs as needed
]