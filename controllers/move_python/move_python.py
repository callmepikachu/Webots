from controller import Robot, TouchSensor, Motion

# Constants
TIME_STEP = 40  # Control step

# Initialize the robot
robot = Robot()

# Get and enable the foot sensors
fsr_left = robot.getDevice('LFsr')  # Left foot sensor
fsr_right = robot.getDevice('RFsr')  # Right foot sensor
fsr_left.enable(TIME_STEP)
fsr_right.enable(TIME_STEP)

# Initialize the robot motion
motion = Motion('../../motions/Forwards.motion')
motion.setLoop(True)
motion.play()

# Count the steps
steps = 0

while robot.step(TIME_STEP) != -1:
    steps += 1

    # Get foot sensor values
    fsv_left = fsr_left.getValues()
    fsv_right = fsr_right.getValues()

    # Calculate left and right foot pressures (optional, can be removed)
    l = [
        fsv_left[2] / 3.4 + 1.5 * fsv_left[0] + 1.15 * fsv_left[1],  # Left Foot Front Left
        fsv_left[2] / 3.4 + 1.5 * fsv_left[0] - 1.15 * fsv_left[1],  # Left Foot Front Right
        fsv_left[2] / 3.4 - 1.5 * fsv_left[0] - 1.15 * fsv_left[1],  # Left Foot Rear Right
        fsv_left[2] / 3.4 - 1.5 * fsv_left[0] + 1.15 * fsv_left[1],  # Left Foot Rear Left
    ]
    r = [
        fsv_right[2] / 3.4 + 1.5 * fsv_right[0] + 1.15 * fsv_right[1],  # Right Foot Front Left
        fsv_right[2] / 3.4 + 1.5 * fsv_right[0] - 1.15 * fsv_right[1],  # Right Foot Front Right
        fsv_right[2] / 3.4 - 1.5 * fsv_right[0] - 1.15 * fsv_right[1],  # Right Foot Rear Right
        fsv_right[2] / 3.4 - 1.5 * fsv_right[0] + 1.15 * fsv_right[1],  # Right Foot Rear Left
    ]

    # Optional: Display foot pressure (could be removed if not needed)
    left_pressure = sum(l)
    right_pressure = sum(r)
    print(f"Left Foot Pressure: {left_pressure} N")
    print(f"Right Foot Pressure: {right_pressure} N")

# Cleanup code
robot.cleanup()
