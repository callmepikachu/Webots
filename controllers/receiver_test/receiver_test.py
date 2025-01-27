from controller import Robot, Receiver
import json

# 初始化机器人和接收器
TIME_STEP = 32
robot = Robot()
receiver = robot.getDevice('receiver')
receiver.enable(TIME_STEP)

def receive_broadcast():
    """
    接收广播数据并解析。
    """
    if receiver.getQueueLength() > 0:
        # 使用 getString() 获取广播消息
        message = receiver.getString()  # 直接获取字符串数据
        receiver.nextPacket()  # 清空已处理的消息

        try:
            # 解析 JSON 数据
            data = json.loads(message)
            robots = data.get("robots", {})
            football = data.get("football", {}).get("position", None)

            # 输出解析后的信息
            print("Received Broadcast:")
            for robot_name, info in robots.items():
                position = info.get("position", [])
                direction = info.get("direction", None)
                print(f"  {robot_name}: Position = {position}, Direction = {direction}")

            if football:
                print(f"  Football Position: {football}")
            else:
                print("  Football position not found.")
        except json.JSONDecodeError:
            print("Failed to decode broadcast message.")


# 主循环
while robot.step(TIME_STEP) != -1:
    receive_broadcast()