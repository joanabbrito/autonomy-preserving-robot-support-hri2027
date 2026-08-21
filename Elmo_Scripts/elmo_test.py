import sys
from asyncio import sleep

from ElmoV2API import ElmoV2API

# Main function
if __name__ == '__main__':
    # We will pass the robot's IP in ter terminal as an argument
    # Note that you need to connect to the app first to discover the IP of the robot
    robot_ip = "192.168.0.108"

    # Initiate the API to communicate with RES request with the robots
    robot = ElmoV2API(robot_ip, debug=True)

    # Check the robot is connected and its current status You can use this command to get information about the
    # battery, what behaviors are active, which files are inside the robot, etc.
    print(robot.status())

    #robot.set_screen(text="Hello there!")

    # Make the robot make sound
    #robot.play_sound("correct.wav")  # sound need to be in .wav

    # Make the robot play a video
    robot.set_screen(video="eyes_green_all.mp4")

    # Reboot the robot
    #robot.reboot()
    # Shutdown the robot
    #robot.shutdown()

