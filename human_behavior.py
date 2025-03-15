import time
import random
import math
import pyautogui

class HumanBehavior:
    def __init__(self):
        # Personality traits that affect behavior (1-10 scale)
        self.speed = random.uniform(3, 8)  # How fast the user moves/types
        self.precision = random.uniform(4, 9)  # How precise mouse movements are
        self.patience = random.uniform(3, 8)  # How long they wait between actions
        self.consistency = random.uniform(5, 9)  # How consistent their timing is
        
        # Calculate derived behavior parameters
        self.base_delay = (11 - self.speed) / 5  # Faster users have shorter delays
        self.delay_variance = (11 - self.consistency) / 10  # Less consistent users have more variance
        self.scroll_style = "smooth" if self.precision > 6 else "jumpy"
        
        print(f"Human behavior profile: Speed={self.speed:.1f}, Precision={self.precision:.1f}, "
              f"Patience={self.patience:.1f}, Consistency={self.consistency:.1f}")
    
    def delay(self, min_seconds=None, max_seconds=None):
        """Add a random delay between actions based on personality"""
        if min_seconds is None:
            min_seconds = max(0.2, self.base_delay * (1 - self.delay_variance))
        if max_seconds is None:
            max_seconds = self.base_delay * (1 + self.delay_variance)
            
        # Add occasional longer pauses (thinking time)
        if random.random() < 0.05:  # 5% chance of a longer pause
            max_seconds *= self.patience / 3
            
        # Add micro-variations in timing
        micro_adjustment = random.gauss(0, 0.1)
        delay_time = random.uniform(min_seconds, max_seconds) + micro_adjustment
        delay_time = max(0.05, delay_time)  # Ensure minimum delay
        
        time.sleep(delay_time)
    
    def move_mouse(self, page, x, y, steps=None):
        """Move mouse in a human-like curve with acceleration and deceleration"""
        # Adjust steps based on precision and distance
        current_pos = pyautogui.position()
        start_x, start_y = current_pos[0], current_pos[1]
        
        if steps is None:
            # Calculate distance
            distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
            
            # More precise users use more steps for smoother movement
            base_steps = max(10, min(40, int(distance / 15)))  # Increased minimum steps for visibility
            precision_factor = self.precision / 5
            steps = int(base_steps * precision_factor)
        
        # Create a curved path with acceleration and deceleration
        for i in range(steps + 1):
            progress = i / steps
            
            # Acceleration curve (ease in and out)
            if progress < 0.2:
                # Acceleration phase
                speed_factor = progress * 5  # 0 to 1 over the first 20%
            elif progress > 0.8:
                # Deceleration phase
                speed_factor = (1 - progress) * 5  # 1 to 0 over the last 20%
            else:
                # Constant speed phase
                speed_factor = 1.0
                
            # Adjust speed based on personality
            speed_factor *= (self.speed / 5)
            
            # Add some randomness to the path based on precision
            precision_noise = (10 - self.precision) / 2
            noise_x = random.gauss(0, precision_noise)
            noise_y = random.gauss(0, precision_noise)
            
            # Calculate position along a curved path (bezier curve)
            # Control points for the curve - more pronounced curve for visibility
            cp1x = start_x + (x - start_x) * 0.3 + random.gauss(0, 15)  # Increased randomness
            cp1y = start_y + (y - start_y) * 0.1 + random.gauss(0, 15)
            cp2x = start_x + (x - start_x) * 0.7 + random.gauss(0, 15)
            cp2y = start_y + (y - start_y) * 0.9 + random.gauss(0, 15)
            
            # Cubic Bezier curve formula
            t = progress
            cx = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1x + 3*(1-t)*t**2 * cp2x + t**3 * x
            cy = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1y + 3*(1-t)*t**2 * cp2y + t**3 * y
            
            # Add the noise
            cx += noise_x
            cy += noise_y
            
            # Move to this position
            page.mouse.move(cx, cy)
            
            # Variable delay between movements - slightly slower for visibility
            time.sleep(random.uniform(0.002, 0.015) / speed_factor)  # Increased delay for visibility
    
    def click(self, page, selector):
        """Click on an element with human-like behavior"""
        element = page.query_selector(selector)
        if element:
            # Get element position
            bbox = element.bounding_box()
            if bbox:
                # Calculate a random position within the element, favoring the center
                center_bias = self.precision / 10  # Higher precision means more center-focused
                
                # Generate position with bias toward center
                x_offset = random.gauss(bbox["width"]/2, bbox["width"]/(4 + center_bias*2))
                y_offset = random.gauss(bbox["height"]/2, bbox["height"]/(4 + center_bias*2))
                
                # Clamp within element bounds with padding
                padding = 2
                x = bbox["x"] + max(padding, min(bbox["width"] - padding, x_offset))
                y = bbox["y"] + max(padding, min(bbox["height"] - padding, y_offset))
                
                # Move to element with variable speed
                self.move_mouse(page, x, y)
                
                # Slight pause before clicking (as humans do)
                self.delay(0.05, 0.2)
                
                # Occasionally double-check position with a tiny movement
                if random.random() < 0.3:  # 30% chance
                    micro_adjust_x = x + random.uniform(-2, 2)
                    micro_adjust_y = y + random.uniform(-2, 2)
                    page.mouse.move(micro_adjust_x, micro_adjust_y)
                    self.delay(0.05, 0.1)
                
                # Click with variable pressure duration
                down_time = random.uniform(0.02, 0.08)
                page.mouse.down()
                time.sleep(down_time)
                page.mouse.up()
                
                return True
        return False
    
    def scroll(self, page, distance=None, smooth=None):
        """Perform human-like scrolling with improved smoothness and natural patterns"""
        if distance is None:
            # Random scroll distance with more variation
            base_distance = random.randint(200, 800)
            # Adjust based on patience - less patient users scroll further
            patience_factor = (11 - self.patience) / 5
            distance = int(base_distance * patience_factor)
        
        # Determine if this should be a smooth or jumpy scroll
        if smooth is None:
            smooth = self.scroll_style == "smooth"
        
        if smooth:
            # Much smoother scrolling with more steps and natural easing
            scroll_steps = random.randint(15, 25)  # Increased steps for smoothness
            
            # Use easing function for more natural movement
            for i in range(scroll_steps):
                progress = i / (scroll_steps - 1)
                
                # Different easing functions based on personality
                if self.precision > 7:
                    # Smoother cubic easing
                    eased_progress = 3 * (progress ** 2) - 2 * (progress ** 3)
                else:
                    # Basic sine easing
                    eased_progress = 0.5 - 0.5 * math.cos(progress * math.pi)
                
                # Calculate step distance with easing
                prev_progress = 0 if i == 0 else (i - 1) / (scroll_steps - 1)
                prev_eased = 0 if i == 0 else (0.5 - 0.5 * math.cos(prev_progress * math.pi))
                current_step = distance * (eased_progress - prev_eased)
                
                # Add subtle randomness based on consistency
                randomness = (11 - self.consistency) / 2
                current_step += random.uniform(-randomness, randomness)
                
                # Perform the scroll
                page.mouse.wheel(0, current_step)
                
                # Variable delay between scroll steps based on speed
                time.sleep(random.uniform(0.01, 0.05) * (11 - self.speed) / 10)
            
            # Pause briefly after scrolling (thinking time)
            self.delay(0.2, 0.5)
        else:
            # Jumpy scrolling behavior
            scroll_steps = random.randint(2, 5)  # Fewer steps for jumpier scrolling
            for _ in range(scroll_steps):
                step_distance = distance / scroll_steps
                # Add more randomness for jumpy scrolling
                step_distance += random.uniform(-30, 30)
                page.mouse.wheel(0, step_distance)
                self.delay(0.1, 0.4)
    
    def type_text(self, page, selector, text):
        """Type text with human-like timing and occasional mistakes"""
        # Click on the input field
        self.click(page, selector)
        
        # Type characters with variable speed and occasional mistakes
        i = 0
        while i < len(text):
            char = text[i]
            
            # Occasional typing mistake (based on precision)
            if random.random() < (0.02 * (10 - self.precision) / 10) and i < len(text) - 1:
                # Make a mistake
                wrong_char = chr(ord(char) + random.randint(-2, 2))
                page.keyboard.type(wrong_char)
                self.delay(0.1, 0.3)
                
                # Correct the mistake
                page.keyboard.press("Backspace")
                self.delay(0.1, 0.2)
                
                # Continue with correct character
                page.keyboard.type(char)
            else:
                # Type normally
                page.keyboard.type(char)
            
            # Determine delay based on character type and user speed
            if char in " ,.?!":
                # Longer pauses for punctuation and spaces
                time.sleep(random.uniform(0.1, 0.3) * (11 - self.speed) / 10)
            elif char in "\n\r":
                # Even longer pause for new lines
                time.sleep(random.uniform(0.2, 0.5) * (11 - self.speed) / 10)
            else:
                # Normal typing speed with slight variations
                base_delay = (11 - self.speed) / 100
                time.sleep(random.uniform(base_delay * 0.5, base_delay * 1.5))
            
            # Occasional pause while typing (thinking)
            if random.random() < 0.01 * self.patience / 10:
                time.sleep(random.uniform(0.5, 1.5))
            
            i += 1