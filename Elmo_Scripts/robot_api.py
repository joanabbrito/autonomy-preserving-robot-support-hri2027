import ElmoV2API
import threading
import time
from gaze_behaviors import random_look_loop, look_at_participant, look_to_the_left, look_to_the_middle, look_to_the_right
import queue
from session_logger import session_logger

class RobotController:
    def __init__(self, ip, debug=False):
        self.debug = debug
        self.last_sound_time = 0
        self.cmd_queue = None

        if debug:
            self.robot = None
            return

        self.robot = ElmoV2API.ElmoV2API(ip, debug=False)
        self.robot.enable_behavior("look_around", False)
        self.robot.enable_behavior("blush", False)
        self.robot.set_pan_torque(True)
        self.robot.set_tilt_torque(True)
        self.robot.update_leds_icon("elmo_idm.png")

    # ------------------ BASIC ACTIONS ------------------

    def play_sound(self, sound):
        now = time.time()
        # Debounce to prevent overlapping commands and speech echoes
        if (now - self.last_sound_time) < 1.5:
            session_logger.log(f"[ROBOT] Suppressed sound (echo avoidance): {sound}")
            return
        self.last_sound_time = now

        session_logger.log(f"[ROBOT] Play Sound: {sound}")
        if self.robot:
            try:
                self.robot.play_sound(sound)
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print(f"[DEBUG] play_sound: {sound}")

    def stop_all_audio(self):
        session_logger.log("[ROBOT] Stop All Audio invoked")
        if self.robot:
            try:
                self.robot.stop_sound()
                self.robot.stop_audio()
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print("[DEBUG] stop_all_audio")

    def set_screen(self, image=None, text=None):
        if image: session_logger.log(f"[ROBOT] Set Screen Image: {image}")
        elif text: session_logger.log(f"[ROBOT] Set Screen Text: {text}")
        
        if self.robot:
            try:
                if image:
                    self.robot.set_screen(image=image)
                elif text:
                    self.robot.set_screen(text=text)
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print(f"[DEBUG] screen: {image or text}")

    def set_leds_icon(self, name):
        session_logger.log(f"[ROBOT] Set LEDs Icon: {name}")
        if self.robot:
            try:
                self.robot.update_leds_icon(name)
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print(f"[DEBUG] set_leds_icon: {name}")

    def update_leds(self, colour):
        session_logger.log(f"[ROBOT] Set LEDs Icon: {colour}")
        if self.robot:
            try:
                self.robot.update_leds(colour)
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print(f"[DEBUG] set_leds_icon: {colour}")

    def set_volume(self, volume):
        if self.robot:
            try:
                self.robot.set_volume(volume)
            except Exception as e:
                print(f"[Robot error] {e}")
        else:
            print(f"[DEBUG] volume: {volume}")
    
    def start_idle_behavior(self):
        self.set_screen(image="normal.png")
        self.set_leds_icon("elmo_idm.png")
        if self.cmd_queue is not None:
            return
        else:
            self.cmd_queue = queue.Queue()

            thread = threading.Thread(
                target=random_look_loop,
                args=(self.robot, self.cmd_queue),
                daemon=True
            )
            thread.start()

            self.cmd_queue.put("start")

    def stop_idle(self):
        if self.cmd_queue:
            self.cmd_queue.put("stop")

    def resume_idle(self):
        self.set_screen(image="normal.png")
        self.set_leds_icon("elmo_idm.png")
        if self.cmd_queue:
            try:
                self.cmd_queue.put("start")
            except Exception as e:
                print(f"[Robot error] {e}")
    
    def look_at_participant(self):
        if self.robot:
            try:
                look_at_participant(self.robot)
            except Exception as e:
                print(f"[Robot error] {e}")

    def look_left(self):
        if self.robot:
            try:
                look_to_the_left(self.robot)
            except Exception as e:
                print(f"[Robot error] {e}")

    def look_right(self):
        if self.robot:
            try:
                look_to_the_right(self.robot)
            except Exception as e:
                print(f"[Robot error] {e}")

    def look_middle(self):
        if self.robot:
            try:
                look_to_the_middle(self.robot)
            except Exception as e:
                print(f"[Robot error] {e}")

    def shutdown(self):
        if self.cmd_queue:
            self.cmd_queue.put("exit")