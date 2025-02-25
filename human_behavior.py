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
        #current_pos = page.mouse.position
        #start_x, start_y = current_pos["x"], current_pos["y"]
        
        # Start from current position (0,0) if not specified
        start_x, start_y = 0, 0

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
    
    def type_text(self, page, selector, text):
        """Type text with human-like timing"""
        # Click on the input field
        self.click(page, selector)
        
        # Type characters with variable speed
        for char in text:
            page.keyboard.type(char)
            # Longer pauses for space and punctuation
            if char in " ,.?!":
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(random.uniform(0.05, 0.15))