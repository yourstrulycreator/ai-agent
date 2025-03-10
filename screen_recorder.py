import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime

class ScreenRecorder:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.recording = False
        self.writer = None
        self.filename = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def start(self, fps=20.0):
        """Start screen recording"""
        if self.recording:
            print("Recording is already in progress")
            return False
        
        try:
            # Get screen size
            screen_size = pyautogui.size()
            width, height = screen_size
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = os.path.join(self.output_dir, f"linkedin_agent_{timestamp}.mp4")
            
            # Define the codec and create VideoWriter object
            # Use XVID codec instead of mp4v for better compatibility
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(self.filename, fourcc, fps, (width, height))
            
            self.recording = True
            print(f"Started screen recording: {self.filename}")
            
            return True
            
        except Exception as e:
            print(f"Error starting screen recording: {e}")
            return False
    
    def capture_frame(self):
        """Capture a single frame"""
        if not self.recording or self.writer is None:
            return False
        
        try:
            # Capture screen
            screenshot = pyautogui.screenshot()
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert from RGB to BGR (OpenCV uses BGR)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Write frame
            self.writer.write(frame)
            
            return True
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False
    
    def record(self, duration=60, fps=20.0):
        """Record for a specific duration in seconds"""
        if not self.start(fps=fps):
            return False
        
        try:
            start_time = time.time()
            frame_time = 1.0 / fps
            next_frame_time = start_time
            
            while time.time() - start_time < duration:
                current_time = time.time()
                
                if current_time >= next_frame_time:
                    self.capture_frame()
                    # Calculate next frame time accounting for processing delays
                    next_frame_time = max(next_frame_time + frame_time, current_time)
                else:
                    # Small sleep to prevent CPU overuse
                    time.sleep(0.001)
            
            self.stop()
            return True
            
        except Exception as e:
            print(f"Error during recording: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop recording"""
        if not self.recording:
            return False
        
        try:
            self.recording = False
            if self.writer:
                self.writer.release()
                print(f"Screen recording saved: {self.filename}")
            
            return True
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False

# Example usage:
# recorder = ScreenRecorder()
# recorder.record(duration=30, fps=20)