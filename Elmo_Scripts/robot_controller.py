# robot_controller.py

import random
import time
import queue
import threading

class RobotController:
    def __init__(self, robot):
        self.robot = robot
        self.cmd_queue = queue.Queue()
        self.thread = threading.Thread(target=self._behavior_loop, daemon=True)
        self.thread.start()

    def start_look(self):
        self.cmd_queue.put("look_on")

    def stop_look(self):
        self.cmd_queue.put("look_off")

    def say(self, sound):
        if self.robot:
            self.robot.play_sound(sound)

    def _behavior_loop(self):
        active = False

        while True:
            try:
                cmd = self.cmd_queue.get_nowait()
                if cmd == "look_on":
                    active = True
                elif cmd == "look_off":
                    active = False
            except:
                pass

            if active:
                self._random_look()

            time.sleep(0.1)

    def _random_look(self):
        status = self.robot.status()
        pan = status["pan"] + random.uniform(-6, 6)
        tilt = status["tilt"] + random.uniform(-2, 2)

        self.robot.set_pan(pan)
        self.robot.set_tilt(tilt)