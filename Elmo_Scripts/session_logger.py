import os
import time

class SessionLogger:
    def __init__(self):
        self.log_file = None
        self.participant_name = ""

    def start_session(self, participant_name):
        if not participant_name or not participant_name.strip():
            self.log_file = None
            self.participant_name = ""
            return

        self.participant_name = participant_name.strip()
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{self.participant_name}_{timestamp}.log"
        self.log_file = os.path.join(log_dir, filename)
        
        self.log(f"--- SESSION STARTED FOR: {self.participant_name} ---")

    def log(self, message):
        if not self.log_file:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"[Logger error] Failed to write log: {e}")

session_logger = SessionLogger()
