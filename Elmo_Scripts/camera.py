import cv2
import threading
import os
from PIL import Image, ImageTk

class CameraManager:
    def __init__(self, url):
        self.url = url
        self.cap = None
        self.latest_frame = None
        self.running = False
        self.lock = threading.Lock()
        
        self.video_writer = None
        self.recording = False
        self.video_filename = None

    def start_recording(self, filename):
        with self.lock:
            self.recording = True
            self.video_filename = filename

    def stop_recording(self):
        with self.lock:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None

    def start(self):
        """Starts the background capture thread."""
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        """Continuously pulls frames from the MJPEG stream in a background thread."""
        self.cap = cv2.VideoCapture(self.url)
        # Low buffer size is critical for minimizing lag on MJPEG streams
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.latest_frame = frame
                    
                    if self.recording:
                        if self.video_writer is None:
                            # Initialize video writer on first recorded frame
                            h, w = frame.shape[:2]
                            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                            # 15 fps is a reasonable default for MJPEG streams
                            self.video_writer = cv2.VideoWriter(self.video_filename, fourcc, 15.0, (w, h))
                        if self.video_writer:
                            self.video_writer.write(frame)
            else:
                # If stream drops, attempt a light reconnect
                self.cap.release()
                self.cap = cv2.VideoCapture(self.url)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.stop_recording()

    def update_widget(self, label):
        """Called by the UI thread to pick up the most recent frame captured by the thread."""
        frame = None
        with self.lock:
            if self.latest_frame is not None:
                # We work with a copy or just reference to display
                frame = self.latest_frame
        
        if frame is not None:
            # Convert OpenCV BGR to RGB
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            # Resize to fit your UI
            img = img.resize((800, 480)) 
            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)