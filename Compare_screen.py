import cv2
import numpy as np
import pyautogui
from tkinter import messagebox
import tkinter as tk
import time

# 捕获屏幕
def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot

# 查找图片
#def find_image_on_screen(template_path, threshold=0.9, max_attempts=10, sleep_time=5.0):
def find_image_on_screen(template_path, threshold=0.9, sleep_time=2.0):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    #attempts = 0
    #while attempts < max_attempts:
    while True:
        screen = capture_screen()
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            return max_loc, template.shape
        time.sleep(sleep_time)  # 等待一段时间后再次尝试
        #attempts += 1
    return None, None

# 主函数
def main():
    template_path = '/Users/yanzhang/Documents/VisualStudioCode/python_code/Resource/poe_more.png'  # 替换为你PNG图片的实际路径
    while True:
        location, shape = find_image_on_screen(template_path)
        if location:
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2
            # 鼠标点击中心坐标
            pyautogui.click(center_x, center_y)
            
            # 移动鼠标并再次点击
            pyautogui.moveRel(-150, 148)  # 往左移动150，往下移动148
            pyautogui.click()  # 执行点击操作
            
            # 弹窗提示
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showinfo("操作结果", "已找到并点击图片，然后移动并再次点击了指定位置")
            break  # 找到图片后退出循环
        else:
            print("没有找到图片，等待重试...")

if __name__ == '__main__':
    main()