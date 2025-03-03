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
    
    def start(self, fps=10.0):
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
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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
            
            # Convert from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Write frame
            self.writer.write(frame)
            
            return True
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False
    
    def record(self, duration=60):
        """Record for a specific duration in seconds"""
        if not self.start():
            return False
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                self.capture_frame()
                time.sleep(0.1)  # This fixed sleep time might cause frame rate issues
            
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