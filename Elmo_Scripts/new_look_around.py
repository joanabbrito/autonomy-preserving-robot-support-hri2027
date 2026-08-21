import ElmoV2API
import time
import random
import threading
import queue


PAN_MIN = -20
PAN_MAX = 55
TILT_MIN = 0
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

    robot.set_pan_torque(True)
    robot.set_tilt_torque(True)

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
        status = robot.status()

        if random.random() < 0.7:
            pan_target = status["pan"] + random.uniform(-8, 8)
            tilt_target = status["tilt"] + random.uniform(-3, 3)
        else:
            pan_target = random.uniform(PAN_MIN, PAN_MAX)
            tilt_target = random.uniform(TILT_MIN, TILT_MAX)

        pan_target = clamp(pan_target, PAN_MIN, PAN_MAX)
        tilt_target = clamp(tilt_target, TILT_MIN, TILT_MAX)

        robot.set_pan(pan_target)
        robot.set_tilt(tilt_target)

        time.sleep(random.uniform(1.5, 3.5))

        status = robot.status()
        robot.set_pan(clamp(status["pan"] + random.uniform(-2, 2), PAN_MIN, PAN_MAX))
        robot.set_tilt(clamp(status["tilt"] + random.uniform(-1, 1), TILT_MIN, TILT_MAX))

        time.sleep(random.uniform(0.8, 1.5))


def look_at_participant(robot):
    if robot is not None:
        robot.enable_behavior("look_around", False)
        time.sleep(1)
        robot.set_pan_torque(True)
        time.sleep(1)
        robot.set_pan(0)  # look straight ahead
        time.sleep(1)
        robot.set_tilt_torque(True)
        time.sleep(1)
        robot.set_tilt(0)


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
    print("Start looking")
    cmd_queue.put("start")

    time.sleep(10)

    print("Stop looking")
    cmd_queue.put("stop")

    time.sleep(5)

    print("Start again")
    cmd_queue.put("start")

    time.sleep(10)

    print("Exit")
    cmd_queue.put("exit")
    behavior_thread.join()


if __name__ == "__main__":
    main()