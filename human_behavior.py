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
    
    def scroll(self, page, distance=None, smooth=True):
        """Perform human-like scrolling with improved smoothness"""
        if distance is None:
            # Random scroll distance with more variation
            distance = random.randint(200, 1000)
        
        if smooth:
            # Much smoother scrolling with more steps and natural easing
            scroll_steps = random.randint(15, 25)  # Increased steps for smoothness
            
            # Use easing function for more natural movement
            for i in range(scroll_steps):
                progress = i / (scroll_steps - 1)
                # Easing function: ease in and out
                eased_progress = 0.5 - 0.5 * math.cos(progress * math.pi)
                
                # Calculate step distance with easing
                current_step = distance * (eased_progress - (0 if i == 0 else (i - 1) / (scroll_steps - 1)))
                
                # Add subtle randomness
                current_step += random.uniform(-5, 5)
                
                # Perform the scroll
                page.mouse.wheel(0, current_step)
                
                # Variable delay between scroll steps
                time.sleep(random.uniform(0.01, 0.05))
            
            # Pause briefly after scrolling
            self.delay(0.3, 0.7)
        else:
            # Original scrolling behavior as fallback
            scroll_steps = random.randint(3, 8)
            for _ in range(scroll_steps):
                step_distance = distance / scroll_steps
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