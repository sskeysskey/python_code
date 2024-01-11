import cv2
import numpy as np
import pyautogui
import time
import threading
from tkinter import messagebox
import tkinter as tk

# 捕获屏幕
def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    return screenshot

# 查找图片
def find_image_on_screen(template_path, threshold=0.9):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    while True:
        screen = capture_screen()
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            return max_loc, template.shape
        time.sleep(1.0)  # 等待一秒后再次尝试

# 执行点击操作
def perform_click_actions(location, shape):
    center_x = (location[0] + shape[1] // 2) // 2
    center_y = (location[1] + shape[0] // 2) // 2
    pyautogui.click(center_x, center_y)
    pyautogui.moveRel(-150, 148)  # 往左移动150，往下移动148
    pyautogui.click()  # 执行点击操作

    # 在UI线程中创建提示框
    #root = tk.Tk()
    #root.withdraw()  # 隐藏主窗口
    #messagebox.showinfo("操作结果", "已找到并点击图片，然后移动并再次点击了指定位置")
    #root.destroy()

# 后台线程任务
def background_task(template_path):
    location, shape = find_image_on_screen(template_path)
    if location:
        perform_click_actions(location, shape)

# 主函数
def main():
    template_path = '/Users/yanzhang/Documents/VisualStudioCode/python_code/Resource/poe_more.png'  # 替换为你PNG图片的实际路径

    # 创建并启动后台线程
    thread = threading.Thread(target=background_task, args=(template_path,))
    thread.daemon = True  # 设置为守护线程，这样主程序结束时子线程也会结束
    thread.start()

    # 这里可以继续执行其他任务，GUI事件循环，或任何其他任务
    # 确保主线程活跃，以便守护线程可以运行
    # ...

if __name__ == '__main__':
    main()