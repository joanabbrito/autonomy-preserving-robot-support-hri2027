import ElmoV2API
import time
import random
import threading
import queue


PAN_MIN = -25
PAN_MAX = 15
#TILT_MIN = 0
TILT_MIN = 15 # TO TRY AND USE THE ROBOT'S CAMERA AS SETUP CAMERA, LIMIT DOWNWARD TILT
TILT_MAX = 15



def clamp(value, vmin, vmax):
    return max(vmin, min(vmax, value))


def random_look_loop(robot, command_queue):
    """
    Runs forever. Starts/stops random look behavior based on queue commands.
    Commands:
        "start" -> begin looking around
        "stop"  -> pause behavior
        "exit"  -> terminate thread
    """
    active = False
    mock_status = {"pan": 0.0, "tilt": 0.0}

    if robot is not None:
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
    else:
        print("[DEBUG] random_look_loop: initialized (mocking movement)")

    def interruptible_sleep(duration):
        nonlocal active
        end_time = time.time() + duration
        while time.time() < end_time:
            try:
                cmd = command_queue.get_nowait()
                if cmd == "start": active = True
                elif cmd == "stop": 
                    active = False
                    return "stop"
                elif cmd == "exit": return "exit"
            except queue.Empty:
                pass
            if not active:
                return "stop"
            time.sleep(0.1)
        return None

    while True:
        # ---- check for commands (non-blocking) ----
        try:
            cmd = command_queue.get_nowait()

            if cmd == "start":
                active = True

            elif cmd == "stop":
                active = False

            elif cmd == "exit":
                break

        except queue.Empty:
            pass

        if not active:
            time.sleep(0.1)
            continue

        # ---- choose movement ----
        if robot is not None:
            status = robot.status() or {}
        else:
            status = mock_status

        if random.random() < 0.7:
            pan_target = status.get("pan", 0) + random.uniform(-8, 8)
            tilt_target = status.get("tilt", 0) + random.uniform(-3, 3)
        else:
            pan_target = random.uniform(PAN_MIN, PAN_MAX)
            tilt_target = random.uniform(TILT_MIN, TILT_MAX)

        pan_target = clamp(pan_target, PAN_MIN, PAN_MAX)
        tilt_target = clamp(tilt_target, TILT_MIN, TILT_MAX)

        if robot is not None:
            robot.set_pan(pan_target)
            robot.set_tilt(tilt_target)
        else:
            mock_status["pan"] = pan_target
            mock_status["tilt"] = tilt_target
            print(f"[DEBUG] random_look_loop: set_pan({pan_target:.2f}), set_tilt({tilt_target:.2f})")

        if interruptible_sleep(random.uniform(1.5, 3.5)) in ("stop", "exit"):
            if not active: continue
            break

        if robot is not None:
            status = robot.status()
        else:
            status = mock_status
        if not status: status = {"pan": 0, "tilt": 0}
        
        pan_target = clamp(status.get("pan", 0) + random.uniform(-2, 2), PAN_MIN, PAN_MAX)
        tilt_target = clamp(status.get("tilt", 0) + random.uniform(-1, 1), TILT_MIN, TILT_MAX)

        if robot is not None:
            robot.set_pan(pan_target)
            robot.set_tilt(tilt_target)
        else:
            mock_status["pan"] = pan_target
            mock_status["tilt"] = tilt_target
            print(f"[DEBUG] random_look_loop: set_pan({pan_target:.2f}), set_tilt({tilt_target:.2f})")

        if interruptible_sleep(random.uniform(0.8, 1.5)) == "exit":
            break


def look_at_participant(robot):
    if robot is not None:
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_pan(0)  # look straight ahead
        robot.set_tilt(-5)

def look_to_the_right(robot):
    if robot is not None:
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_tilt(15) # tilt head down a bit
        robot.set_pan(-25) # robot looks to the right

def look_to_the_left(robot):
    if robot is not None:
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_tilt(15) 
        robot.set_pan(20) # robot looks to the left

def look_to_the_middle(robot):
    if robot is not None:
        robot.set_pan_torque(True)
        robot.set_tilt_torque(True)
        robot.set_tilt(15) 
        robot.set_pan(0) # robot looks straight


def main():
    robot_ip = "192.168.0.107"
    robot = ElmoV2API.ElmoV2API(robot_ip, debug=False)

    

    cmd_queue = queue.Queue()
    behavior_thread = threading.Thread(
        target=random_look_loop,
        args=(robot, cmd_queue),
        daemon=True
    )
    behavior_thread.start()

    # ---- example usage ----
    #print("Start looking")
    #cmd_queue.put("start")

    #time.sleep(3)

    

    #print("Stop looking")
    #cmd_queue.put("stop")

    look_at_participant(robot)

    #time.sleep(5)

    #print("Start again")
    #cmd_queue.put("start")

    #time.sleep(10)

    #print("Exit")
    #cmd_queue.put("exit")
    #behavior_thread.join()


if __name__ == "__main__":
    main()