from controller import Robot, Camera, Motion
import numpy as np
import cv2

# Webots 控制器时间步长
TIME_STEP = 16

# 创建机器人对象
robot = Robot()

# 获取顶部和底部摄像头及运动设备
cameraTop = robot.getDevice('CameraTop')
cameraTop.enable(TIME_STEP)
cameraBottom = robot.getDevice('CameraBottom')  # 新增底部摄像头
cameraBottom.enable(TIME_STEP)

motion_forward = Motion("../../motions/Forwards.motion")  # 前进
motion_backward = Motion("../../motions/Backwards.motion")  # 后退
hand_wave_motion = Motion("../../motions/HandWave.motion")  # 挥手
turn_left_motion = Motion("../../motions/TurnLeft40.motion")  # 左转40°
turn_right_motion = Motion("../../motions/TurnRight60.motion")  # 右转60°
Shoot_motion = Motion("../../motions/Shoot.motion")  # 射门

# 定义机器人状态
STATE_VISION = 1
STATE_MOVE_FORWARD = 2
STATE_MOVE_BACKWARD = 3
STATE_HAND_WAVE = 4
STATE_TURN_LEFT = 5
STATE_TURN_RIGHT = 6
STATE_SHOOT = 7
state = STATE_VISION  # 初始状态为视觉检查

# 初始化状态变量
previous_state = None
right_turn_count = 0
left_turn_count = 0
backward_count = 0
movement_flag = None
hand_waved = 0
bottom_camera_lost_ball = False  # 标记cameraBottom是否从看到球变为看不到球

# 定义函数：进行顶部摄像头的视觉检查
def initial_vision_check():
    print("Performing initial vision check...")
    img_data = cameraTop.getImage()
    if img_data is None:
        print("Failed to get image from camera.")
        return None

    image = np.frombuffer(img_data, dtype=np.uint8).reshape((cameraTop.getHeight(), cameraTop.getWidth(), 4))
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    output_image, centroid, ball_position = replace_green_with_red(image)

    if ball_position == "center":
        return STATE_MOVE_FORWARD
    elif ball_position == "left":
        return STATE_TURN_LEFT
    elif ball_position == "right":
        return STATE_TURN_RIGHT
    else:
        return None  # 未检测到球

# 定义函数：底部摄像头的视觉检查
def initial_bottom_camera_check():
    print("Performing bottom camera vision check...")
    img_data = cameraBottom.getImage()
    if img_data is None:
        print("Failed to get image from bottom camera.")
        return None

    image = np.frombuffer(img_data, dtype=np.uint8).reshape((cameraBottom.getHeight(), cameraBottom.getWidth(), 4))
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    output_image, centroid, ball_position = replace_green_with_red(image)

    if ball_position == "center":
        return STATE_MOVE_FORWARD
    elif ball_position == "left":
        return STATE_TURN_LEFT
    elif ball_position == "right":
        return STATE_TURN_RIGHT
    else:
        return None  # 未检测到球

# 定义函数：替换绿色区域为红色
def replace_green_with_red(image):
    output_image = image.copy()
    height, width, _ = image.shape

    green_low = np.array([0, 200, 0])
    green_high = np.array([120, 255, 120])

    green_pixels = np.where(
        (image[:, :, 0] >= green_low[0]) & (image[:, :, 1] >= green_low[1]) & (image[:, :, 2] >= green_low[2]) &
        (image[:, :, 0] <= green_high[0]) & (image[:, :, 1] <= green_high[1]) & (image[:, :, 2] <= green_high[2])
    )

    output_image[green_pixels] = [255, 0, 0]

    if green_pixels[0].size > 0:
        centroid = np.mean(np.array([green_pixels[0], green_pixels[1]]), axis=1).astype(int)
    else:
        centroid = [np.nan, np.nan]

    left_boundary = width // 3
    right_boundary = 2 * width // 3
    cv2.line(output_image, (left_boundary, 0), (left_boundary, height), (255, 255, 255), 2)
    cv2.line(output_image, (right_boundary, 0), (right_boundary, height), (255, 255, 255), 2)

    if not np.isnan(centroid[0]):
        if centroid[1] < left_boundary:
            ball_position = "left"
            cv2.circle(output_image, (left_boundary // 2, height // 2), 10, (0, 0, 255), -1)
        elif centroid[1] < right_boundary:
            ball_position = "center"
            cv2.circle(output_image, ((left_boundary + right_boundary) // 2, height // 2), 10, (0, 0, 255), -1)
        else:
            ball_position = "right"
            cv2.circle(output_image, ((right_boundary + width) // 2, height // 2), 10, (0, 0, 255), -1)
    else:
        ball_position = None

    cv2.imshow("Ball Position Detection", output_image)
    cv2.waitKey(1)

    return output_image, centroid, ball_position

# 机器人运动函数
def move_forward():
    print("Moving forward...")
    motion_forward.setLoop(False)
    motion_forward.play()
    while robot.step(TIME_STEP) != -1:
        if motion_forward.isOver():
            break

def move_backward():
    print("Moving backward...")
    motion_backward.setLoop(False)
    motion_backward.play()
    while robot.step(TIME_STEP) != -1:
        if motion_backward.isOver():
            break

def perform_hand_wave():
    print("Performing hand wave...")
    hand_wave_motion.play()
    while robot.step(TIME_STEP) != -1:
        if hand_wave_motion.isOver():
            break

def turn_left():
    print("Turning left 40 degrees...")
    turn_left_motion.setLoop(False)
    turn_left_motion.play()
    while robot.step(TIME_STEP) != -1:
        if turn_left_motion.isOver():
            break

def turn_right():
    print("Turning right 60 degrees...")
    turn_right_motion.setLoop(False)
    turn_right_motion.play()
    while robot.step(TIME_STEP) != -1:
        if turn_right_motion.isOver():
            break

def shoot():
    print("Shooting...")
    Shoot_motion.setLoop(False)
    Shoot_motion.play()
    while robot.step(TIME_STEP) != -1:
        if Shoot_motion.isOver():
            break

# 状态机控制逻辑
def state_machine():
    global state, previous_state, right_turn_count, left_turn_count, movement_flag, bottom_camera_lost_ball

    state_actions = {
        STATE_VISION: handle_vision,
        STATE_MOVE_FORWARD: move_forward_state,
        STATE_MOVE_BACKWARD: move_backward_state,
        STATE_HAND_WAVE: perform_hand_wave_state,
        STATE_TURN_LEFT: turn_left_state,
        STATE_TURN_RIGHT: turn_right_state,
        STATE_SHOOT: shoot_state
    }

    while robot.step(TIME_STEP) != -1:
        state_actions[state]()

# 状态处理函数
def handle_vision():
    global state, previous_state, right_turn_count, left_turn_count, hand_waved, bottom_camera_lost_ball
    next_state = initial_vision_check()
    
    if next_state is None:
        bottom_camera_state = initial_bottom_camera_check()
        if bottom_camera_state is not None:
            state = bottom_camera_state
            bottom_camera_lost_ball = False
            reset_turn_counts()
        else:
            if not bottom_camera_lost_ball:
                bottom_camera_lost_ball = True
                state = STATE_SHOOT
            else:
                if right_turn_count < 3:
                    state = STATE_TURN_RIGHT
                    right_turn_count += 1
                elif left_turn_count < 3:
                    state = STATE_TURN_LEFT
                    left_turn_count += 1
                else:
                    if hand_waved == 0:
                        state = STATE_HAND_WAVE
                        hand_waved = 1
                    else:
                        state = STATE_MOVE_BACKWARD
                        hand_waved = 0
    else:
        state = next_state
        bottom_camera_lost_ball = False
        reset_turn_counts()

def move_forward_state():
    global state
    move_forward()
    state = STATE_VISION

def move_backward_state():
    global state, backward_count
    move_backward()
    backward_count += 1
    if backward_count >= 3:
        state = STATE_VISION
        backward_count = 0
    else:
        state = STATE_MOVE_BACKWARD

def perform_hand_wave_state():
    global state
    perform_hand_wave()
    state = STATE_VISION

def turn_left_state():
    global state
    turn_left()
    state = STATE_VISION

def turn_right_state():
    global state
    turn_right()
    state = STATE_VISION

def shoot_state():
    global state
    shoot()
    state = STATE_VISION

def reset_turn_counts():
    global right_turn_count, left_turn_count
    right_turn_count = 0
    left_turn_count = 0

# 主函数
if __name__ == "__main__":
    state_machine()
