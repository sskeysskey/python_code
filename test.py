import re
import os
import cv2
import pyperclip
import pyautogui
from time import sleep
from datetime import datetime

def capture_screen():
    # 定义截图路径
    screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
    # 使用pyautogui截图并直接保存
    pyautogui.screenshot(screenshot_path)
    # 读取刚才保存的截图文件
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    # 确保screenshot已经正确加载
    if screenshot is None:
        raise FileNotFoundError(f"截图未能正确保存或读取于路径 {screenshot_path}")
    # 返回读取的截图数据
    return screenshot

# 查找图片
def find_image_on_screen(template_path, threshold=0.9):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"模板图片未能正确读取于路径 {template_path}")
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # 释放截图和模板图像以节省内存
    del screen
    if max_val >= threshold:
        return max_loc, template.shape
    else:
        return None, None

# 检查 soldout.png 是否存在于屏幕上
def check_soldout_image():
    remaining_template_path = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout.png'  # 替换为你的remaining.png图片实际路径
    location, shape = find_image_on_screen(remaining_template_path, threshold=0.9)
    return bool(location)

# 设置stop_signal文件的保存目录
stop_signal_directory = '/private/tmp'
            
            # 设置stop_signal文件的保存路径
now = datetime.now()
time_str = now.strftime("_%y_%m_%d")
stop_signal_file_name = f"stop_signal{time_str}.txt"
stop_signal_path = os.path.join(stop_signal_directory, stop_signal_file_name)

            # 检查 soldout.png 是否存在于屏幕上
            
                # 如果存在，则运行另一个Python脚本
if check_soldout_image():
    with open(stop_signal_path, 'w') as signal_file:
        signal_file.write('stop')
else:
    print("未找到A图片，继续监控...")
            