import datetime
import numpy as np
import cv2
import pyautogui
import os
import time
import threading

class ScreenRecorder:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.recording = False
        self.writer = None
        self.filename = None
        self.thread = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def start(self, fps=10.0):  # Reduced FPS for better stability
        """Start screen recording"""
        if self.recording:
            print("Recording is already in progress")
            return False
        
        try:
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            # Generate filename with timestamp
            time_stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            self.filename = os.path.join(self.output_dir, f'linkedin_agent_{time_stamp}.mp4')
            
            # Define the codec and create VideoWriter object
            # Use H264 codec which is more widely supported
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Changed from mp4v to avc1 (H.264)
            self.writer = cv2.VideoWriter(
                self.filename, 
                fourcc, 
                fps, 
                (screen_width, screen_height)
            )
            
            # Verify that the writer was properly initialized
            if not self.writer.isOpened():
                print("Failed to initialize video writer")
                return False
                
            self.recording = True
            print(f"Started screen recording: {self.filename}")
            
            # Start recording in a separate thread
            self.thread = threading.Thread(target=self._record_thread, args=(fps,))
            self.thread.daemon = True
            self.thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting screen recording: {e}")
            if self.writer:
                self.writer.release()
                self.writer = None
            return False
    
    def _record_thread(self, fps):
        """Background thread for continuous recording"""
        frame_time = 1.0 / fps
        next_frame_time = time.time()
        
        while self.recording:
            try:
                current_time = time.time()
                
                if current_time >= next_frame_time:
                    self.capture_frame()
                    # Calculate next frame time accounting for processing delays
                    next_frame_time = max(next_frame_time + frame_time, current_time)
                else:
                    # Small sleep to prevent CPU overuse
                    time.sleep(0.001)
            except Exception as e:
                print(f"Error in recording thread: {e}")
                time.sleep(0.1)  # Add delay to prevent rapid error logging
    
    def capture_frame(self):
        """Capture a single frame"""
        if not self.recording or self.writer is None:
            return False
        
        try:
            # Capture screen using pyautogui (works on macOS)
            img = pyautogui.screenshot()
            
            # Convert to numpy array
            img_np = np.array(img)
            
            # Convert from RGB to BGR (OpenCV uses BGR)
            img_final = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # Write frame
            self.writer.write(img_final)
            
            return True
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False
    
    def record(self, duration=60, fps=10.0):  # Reduced FPS for better stability
        """Record for a specific duration in seconds"""
        if not self.start(fps=fps):
            return False
        
        try:
            # Sleep for the duration
            time.sleep(duration)
            
            # Stop recording
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
            
            # Wait for recording thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)  # Increased timeout
            
            if self.writer:
                self.writer.release()
                print(f"Screen recording saved: {self.filename}")
                self.writer = None
            
            return True
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False

# Example usage:
# recorder = ScreenRecorder()
# recorder.start()  # Start recording in background
# # Do other things...
# recorder.stop()   # Stop when done