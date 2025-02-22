from controller import Supervisor, Camera, Motion
import numpy as np
import cv2

# 球场中点坐标(0,0),红队右底角(-4.5,-3), 左底角(4.5,-3), 蓝队右底角,,, 球门(-4.5,0) , x轴是进攻方向


# 时间步长
TIME_STEP = 16

# 创建 Supervisor 对象
robot = Supervisor()

# 初始化摄像头和运动设备
cameraTop = robot.getDevice('CameraTop')
cameraTop.enable(TIME_STEP)
cameraBottom = robot.getDevice('CameraBottom')
cameraBottom.enable(TIME_STEP)

motion_forward = Motion("../../motions/Forwards.motion")
motion_backward = Motion("../../motions/Backwards.motion")
hand_wave_motion = Motion("../../motions/HandWave.motion")
turn_left_motion = Motion("../../motions/TurnLeft40.motion")
turn_right_motion = Motion("../../motions/TurnRight60.motion")
Shoot_motion = Motion("../../motions/Shoot.motion")


def get_robots_and_football():
    robot_names  = ['red 1', 'red 2', 'red 3', 'red 4', 'blue 1', 'blue 2', 'blue 3', 'blue 4']
    football = None
    robots = {}

    root = robot.getRoot()
    children = root.getField("children")

    for i in range(children.getCount()):
        node = children.getMFNode(i)

        # 查找football节点
        if node.getField("name") and node.getField("name").getSFString() == "football":
            football = node
        # 查找指定的机器人节点
        for name in robot_names:
            if node.getField("name") and node.getField("name").getSFString() == name:
                robots[name]=(node)

    if football is None:
        raise ValueError("Error: Football node not found in the world file.")

    if robots is None or len(robots) == 0:
        raise ValueError("Error: Robots node not found in the world file.")

    return football, robots



# 存储位置数据
positions = {}

# 定义状态机状态
STATE_VISION = 1
STATE_MOVE_FORWARD = 2
STATE_MOVE_BACKWARD = 3
STATE_HAND_WAVE = 4
STATE_TURN_LEFT = 5
STATE_TURN_RIGHT = 6
STATE_SHOOT = 7
state = STATE_VISION

# 定义函数：替换绿色区域为红色
def replace_green_with_red(image):
    output_image = image.copy()
    height, width, _ = image.shape
    green_low = np.array([200, 100, 0])
    green_high = np.array([255, 200, 50])

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


# 获取机器人和足球的位置并存储
def update_positions():
    football, robots_dict = get_robots_and_football()
    robots = robots_dict.values()
    global positions
    positions = {}

    # 将 dict_keys 转换为列表以便索引
    robot_names = list(robots_dict.keys())

    for i, r in enumerate(robots):
        if r is not None:
            pos = r.getPosition()
            positions[robot_names[i]] = pos  # 使用 robot_names[i] 作为键

    if football is not None:
        football_pos = football.getPosition()
        positions['football'] = football_pos


# 打印和存储机器人和足球的坐标
def log_positions():
    print("Current positions:")
    for name, pos in positions.items():
        print(f"{name}: {pos}")

# 状态机控制逻辑
def state_machine():
    global state
    while robot.step(TIME_STEP) != -1:
        update_positions()
        log_positions()

        if state == STATE_VISION:
            # 视觉检测逻辑（保留原有逻辑）
            state = STATE_MOVE_FORWARD  # 示例：直接切换到前进状态
        elif state == STATE_MOVE_FORWARD:
            print("Moving forward...")
            motion_forward.play()
            while robot.step(TIME_STEP) != -1:
                if motion_forward.isOver():
                    break
            state = STATE_VISION
        elif state == STATE_MOVE_BACKWARD:
            print("Moving backward...")
            motion_backward.play()
            while robot.step(TIME_STEP) != -1:
                if motion_backward.isOver():
                    break
            state = STATE_VISION
        elif state == STATE_HAND_WAVE:
            print("Performing hand wave...")
            hand_wave_motion.play()
            while robot.step(TIME_STEP) != -1:
                if hand_wave_motion.isOver():
                    break
            state = STATE_VISION
        elif state == STATE_TURN_LEFT:
            print("Turning left...")
            turn_left_motion.play()
            while robot.step(TIME_STEP) != -1:
                if turn_left_motion.isOver():
                    break
            state = STATE_VISION
        elif state == STATE_TURN_RIGHT:
            print("Turning right...")
            turn_right_motion.play()
            while robot.step(TIME_STEP) != -1:
                if turn_right_motion.isOver():
                    break
            state = STATE_VISION
        elif state == STATE_SHOOT:
            print("Shooting...")
            Shoot_motion.play()
            while robot.step(TIME_STEP) != -1:
                if Shoot_motion.isOver():
                    break
            state = STATE_VISION

# 启动状态机
state_machine()
