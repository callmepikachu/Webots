from controller import Supervisor, Camera, Motion
import numpy as np
import cv2

# 球场中点坐标(0,0),红队右底角(-4.5,-3), 左底角(4.5,-3), 蓝队右底角,,, 球门(-4.5,0) , x轴是进攻方向


# 时间步长
TIME_STEP = 16

# 创建 Supervisor 对象
robot = Supervisor()

me = "red 2"

positions = {}
directions = {}

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
STATE_MOVE_TO_POSITION = 8


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
    # 将 dict_keys 转换为列表以便索引
    robot_names = list(robots_dict.keys())

    for i, r in enumerate(robots):
        if r is not None:
            pos = r.getPosition()
            positions[robot_names[i]] = pos  # 使用 robot_names[i] 作为键
            direction = r.getOrientation()
            directions[robot_names[i]] = direction

    if football is not None:
        football_pos = football.getPosition()
        positions['football'] = football_pos


# 打印和存储机器人和足球的坐标
def log_positions():
    print("Current positions:")
    for name, pos in positions.items():
        print(f"{name}: {pos}")

# 计算中点
def calculate_midpoint(pos1, pos2):
    """计算两点的中点"""
    return [(pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2, (pos1[2] + pos2[2]) / 2]

# 调整射门位置
def adjust_position_for_shooting(football_pos):
    """调整射门位置，考虑机器人尺寸偏移"""
    robot_radius = 0.2  # 假设机器人半径为 0.2
    return [football_pos[0] - robot_radius, football_pos[1]]

# 判断是否到达目标位置
def has_arrived_at_position(target_pos, threshold=0.1):
    """判断机器人是否到达目标位置"""
    current_pos = positions[me]
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    distance = (dx**2 + dy**2) ** 0.5
    print(f"distance = {distance}")
    return distance < threshold

# 移动到指定位置
import math

def move_to_position(target_pos):
    """
    将机器人移动到目标位置，先调整方向，再移动。
    """
    current_pos = positions[me]
    current_orientation = directions[me]  # 获取当前方向矩阵
    # current_yaw = math.atan2(current_orientation[1], current_orientation[0])  # 计算当前的航向角（绕 Z 轴）
    # current_yaw = current_orientation[3]  # 计算当前的航向角（绕 Z 轴）
    R= np.array(current_orientation).reshape(3, 3)
    roll = math.atan2(R[2, 1], R[2, 2])  # 绕 X 轴的滚动角
    yaw = math.atan2(R[1, 0], R[0, 0])  # 绕 Z 轴的偏航角
    pitch = math.asin(-R[2, 0])  # 绕 Y 轴的俯仰角
    # print(f"当前航向角is {yaw}")
    current_yaw = yaw
    # print(current_orientation)

    # 计算目标方向
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    target_yaw = math.atan2(dy, dx)  # 目标方向的航向角
    # print(f"目标航向角 is {target_yaw}")

    # 计算需要旋转的角度
    delta_yaw =  target_yaw-current_yaw

    # 将角度归一化到 [-π, π] 范围
    while delta_yaw > math.pi:
        delta_yaw -= 2 * math.pi
    while delta_yaw < -math.pi:
        delta_yaw += 2 * math.pi

    # 判断需要左转还是右转
    if abs(delta_yaw) > 1:  # 假设 0.1 弧度内为精度范围
        print(f"delta_yaw = {delta_yaw}")
        if delta_yaw > 0:
            print("Turning left...")
            turn_left_motion.play()
            while robot.step(TIME_STEP) != -1:
                if turn_left_motion.isOver() :
                    break
        else:
            print("Turning right...")
            turn_right_motion.play()
            while robot.step(TIME_STEP) != -1:
                if turn_right_motion.isOver() :
                    break
    else:
        # 完成转向后，开始移动
        distance = math.sqrt(dx**2 + dy**2)  # 计算目标点的平面距离
        if distance > 0.1:  # 如果距离足够大，则移动
            print("Moving forward...")
            motion_forward.play()
            while robot.step(TIME_STEP) != -1:
                if motion_forward.isOver():
                            break

    print(f"Arrived at position: {target_pos}")

# 主状态机
def state_machine():
    global state
    while robot.step(TIME_STEP) != -1:
        update_positions()  # 更新所有位置
        # log_positions()  # 打印位置日志

        striker_pos = positions.get("red 1", None)
        football_pos = positions.get("football", None)

        if not striker_pos or not football_pos:
            print("Waiting for position updates...")
            continue

        # 根据状态机逻辑进行状态转移
        if state == STATE_VISION:  # 初始或等待状态
            print(f"football_pos={football_pos[0]},striker_pos = {striker_pos[0]} ")
            if football_pos[0] > striker_pos[0]:
                # 如果球在 striker 的前方，移动到 striker 和底角的中点
                target_pos = calculate_midpoint(striker_pos, [-4.5, -3, 0])# 假设底角为 [0, 0, 0](-4.5,-3)
                print(f"正在前往:striker和底角的中间点, defender is going to {target_pos}")
                state = STATE_MOVE_TO_POSITION
            else:
                # 如果球在 striker 的后方，直接移动到球的位置
                target_pos = adjust_position_for_shooting(football_pos)
                print(f"正在前往:球的位置, defender is going to {target_pos}")
                state = STATE_MOVE_TO_POSITION

        elif state == STATE_MOVE_TO_POSITION:
            print(f"Moving to target position: {target_pos}")
            move_to_position(target_pos)  # 调用移动函数
            if has_arrived_at_position(target_pos):  # 检查是否到达
                if has_arrived_at_position(football_pos, threshold = 0.3):  # 如果目标位置和足球位置相距小于0.1，进入射门状态
                    state = STATE_SHOOT
                else:
                    state = STATE_VISION
            else:
                print(" 还没到位置呢")

        elif state == STATE_SHOOT:
            print("Shooting...")
            Shoot_motion.play()  # 播放射门动作
            while robot.step(TIME_STEP) != -1:
                if Shoot_motion.isOver():
                    break
            state = STATE_VISION  # 返回视觉状态

# 启动状态机
state_machine()
