import config
from browser_agent import BrowserAgent
from data_extractor import DataExtractor
import os

def test_data_extractor():
    print("Testing data extractor...")
    
    # Initialize components
    browser = BrowserAgent(headless=False)
    browser.start()
    extractor = DataExtractor(browser)
    
    try:
        # Test extraction on a public LinkedIn profile or company page
        # Using a company page as it doesn't require login
        test_url = "https://www.linkedin.com/company/microsoft/"
        print(f"Testing data extraction on: {test_url}")
        
        # Extract data
        data = extractor.extract_profile_data(test_url)
        print("Extracted data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        
        # Test saving to CSV
        test_csv = "test_data.csv"
        extractor.save_to_csv(data, test_csv)
        print(f"Data saved to CSV: {test_csv}")
        
        # Test saving to JSON
        test_json = "test_data.json"
        extractor.save_to_json(data, test_json)
        print(f"Data saved to JSON: {test_json}")
        
        # Check if files were created
        print(f"CSV file exists: {os.path.exists(test_csv)}")
        print(f"JSON file exists: {os.path.exists(test_json)}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Close the browser
        browser.close()
        print("Data extractor test completed")

if __name__ == "__main__":
    test_data_extractor()