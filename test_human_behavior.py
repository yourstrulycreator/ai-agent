from playwright.sync_api import sync_playwright
from human_behavior import HumanBehavior
import time

def test_human_behavior():
    print("Testing human behavior simulation...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        human = HumanBehavior()
        
        # Open a test page
        page.goto('https://www.google.com')
        print("Opened Google. Testing behavior...")
        
        # Test delay
        print("Testing delay...")
        human.delay(1, 2)
        print("Delay completed")
        
        # Test mouse movement
        print("Testing mouse movement...")
        human.move_mouse(page, 500, 300)
        print("Mouse movement completed")
        
        # Test scrolling
        print("Testing scrolling...")
        human.scroll(page)
        print("Scrolling completed")
        
        # Test clicking (on Google search box)
        print("Testing clicking...")
        search_box_clicked = human.click(page, 'input[name="q"]')
        print(f"Click succeeded: {search_box_clicked}")
        
        # Test typing
        if search_box_clicked:
            print("Testing typing...")
            human.type_text(page, 'input[name="q"]', "Human behavior test")
            print("Typing completed")
        
        # Wait a moment to observe results
        time.sleep(3)
        browser.close()
        
        print("Human behavior test completed successfully")

if __name__ == "__main__":
    test_human_behavior()