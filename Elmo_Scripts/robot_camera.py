import cv2
import queue
import threading
import ElmoV2API
from gaze_behaviors import random_look_loop

url = "http://192.168.0.107:8080/stream.mjpg"
cap = cv2.VideoCapture(url)

robot_ip = "192.168.0.107"
robot = ElmoV2API.ElmoV2API(robot_ip, debug=False)
#print(robot.status())

#robot.enable_behavior("look_around", False)

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

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Robot Camera", frame)
    if cv2.waitKey(1) == 27:
        break


print("Stop looking")
cmd_queue.put("stop")

cap.release()
cv2.destroyAllWindows()