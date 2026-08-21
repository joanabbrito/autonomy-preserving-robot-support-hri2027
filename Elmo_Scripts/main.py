import tkinter as tk
from robot_api import RobotController
from state_machine import GameState
from gui import create_gui, UI
from config import ROBOT_IP, DEBUG
from camera import CameraManager

def main():
    # 1. Initialize Robot and State
    robot = RobotController(ROBOT_IP, debug=DEBUG)
    state = GameState()

    # 2. Create the Tkinter root window FIRST
    app = tk.Tk()

    # 3. Initialize the UI wrapper with that window
    ui = UI(app)

    camera = CameraManager(url=f"http://{ROBOT_IP}:8080/stream.mjpg")
    camera.start()
    # 4. Now create the GUI elements, passing the initialized 'ui'
    camera_label, status_var = create_gui(robot, state, ui, camera)

    # 3. Start the Camera Update Loop
    def update_cam():
        camera.update_widget(camera_label)
        app.after(30, update_cam)
    update_cam()

    # 5. Start background processes
    robot.start_idle_behavior() # Or start_idle_behavior() depending on your previous fix
    
    print("System initialized. Starting GUI...")
    app.mainloop()
    camera.stop()

if __name__ == "__main__":
    main()