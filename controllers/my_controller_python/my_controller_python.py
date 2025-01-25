from controller import Robot, Camera
import numpy as np
import cv2
import time
import sys
print("Python executable path:", sys.executable)


# 初始化 Webots 控制器
TIME_STEP = 32
robot = Robot()
# 获取所有设备名称
device_names = robot.getDeviceNames()

# 打印设备名称
print("NAO 机器人所有设备名称:")
for name in device_names:
    print(name)
# 定义绿色区域替换函数
def replace_green_with_red(image):
    output_image = image.copy()  # 复制图像以便替换绿色区域
    green_low = np.array([0, 200, 0])       # 绿色下限（RGB）
    green_high = np.array([120, 255, 120])  # 绿色上限（RGB）
    
    # 找到绿色区域，并将其替换为红色
    mask = cv2.inRange(image, green_low, green_high)
    output_image[mask > 0] = [255, 0, 0]
    
    # 提取红色区域的坐标
    red_pixels = np.column_stack(np.where(mask > 0))
    
    # 计算红色区域的几何中心
    if red_pixels.size > 0:
        centroid = np.mean(red_pixels, axis=0)
    else:
        centroid = [np.nan, np.nan]
    
    return output_image, centroid

# 获取 NAO 机器人的头部摄像头
camera = robot.getDevice('CameraTop')
if camera:
    camera.enable(TIME_STEP)
    print('Camera enabled')

    # 打印摄像头图像的长和宽
    img_width = camera.getWidth()
    img_height = camera.getHeight()
    print(f'Camera image dimensions: Width = {img_width}, Height = {img_height}')
else:
    print('Camera device not found')

# 主控制循环
steps = 0
while robot.step(TIME_STEP) != -1:
    img_data = camera.getImage()
    
    if img_data:
        # 转换图像为 NumPy 格式
        img_array = np.frombuffer(img_data, np.uint8).reshape((img_height, img_width, 4))
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
        
        # 显示原始图像
        cv2.imshow('原始图像', img_rgb)
        
        # 检测并替换绿色区域
        output_image, centroid = replace_green_with_red(img_rgb)
        
        # 显示替换后的图像
        cv2.imshow('绿色区域替换为红色', output_image)
        
        # 打印红色区域的几何中心
        if not np.isnan(centroid[0]):
            print(f'Red area centroid: ({centroid[0]:.2f}, {centroid[1]:.2f})')
        else:
            print('No red area detected.')
        
        # 更新显示
        cv2.waitKey(1)
    else:
        print('Failed to retrieve image data')
        
# 清理 Webots 控制器
cv2.destroyAllWindows()
