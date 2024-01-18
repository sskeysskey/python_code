import cv2
import time
import pyperclip
import pyautogui
import numpy as np
import tkinter as tk
from time import sleep
from tkinter import messagebox

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
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        return max_loc, template.shape
    else:
        return None, None

# 主函数
def main():
    template_path = '/Users/yanzhang/Documents/python_code/Resource/poe_stop.png'  # 替换为你PNG图片的实际路径
    while True:
        location, shape = find_image_on_screen(template_path)
        if location:
            print("找到A图片，继续监控...")
            sleep(1)  # 简短暂停再次监控
            
        else:
            pyautogui.click(button='right')
            sleep(0.5)
            # 移动鼠标并再次点击
            pyautogui.moveRel(110, 118)  # 往右移动110，往下移动118
            sleep(0.5)
            pyautogui.click()  # 执行点击操作
            sleep(1)

            # 设置SRT文件的保存路径
            srt_file_path = '/Users/yanzhang/Movies/第三种黑猩猩.txt'

            # 读取剪贴板内容
            clipboard_content = pyperclip.paste()

            # 追加剪贴板内容到SRT文件
            with open(srt_file_path, 'a', encoding='utf-8-sig') as f:
                f.write(clipboard_content)
                f.write('\n\n')  # 添加两个换行符以创建一个空行

            break  # 图片消失后退出循环

if __name__ == '__main__':
    main()