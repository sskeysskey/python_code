import re
import os
import cv2
import sys
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

template_path2 = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout2.png'  # 替换为你PNG图片的实际路径

sleep(2)
while True:
        location, shape = find_image_on_screen(template_path2)
        if location:
            # 设置stop_signal文件的保存目录
            stop_signal_directory = '/private/tmp'
            
            # 设置stop_signal文件的保存路径
            now = datetime.now()
            time_str = now.strftime("_%m_%d_%H")
            stop_signal_file_name = f"stop_signal{time_str}.txt"
            stop_signal_path = os.path.join(stop_signal_directory, stop_signal_file_name)

            with open(stop_signal_path, 'w') as signal_file:
                    signal_file.write('stop')
            sys.exit(0)  # 安全退出程序
        else:
            print("没找到图片，继续执行...")
            break

            