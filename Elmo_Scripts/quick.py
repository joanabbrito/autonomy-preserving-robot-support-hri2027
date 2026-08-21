

from config import ROBOT_IP, DEBUG
import ElmoV2API


def main():             
    # 1. Initialize Robot and State

    robot = ElmoV2API.ElmoV2API(ROBOT_IP, debug=True)
    robot.set_screen("tears.png")


if __name__ == "__main__":
    main()