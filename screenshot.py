import os
import cv2
import sys
import time
import pyautogui
import numpy as np
from time import sleep
from PIL import ImageGrab

class ScreenDetector:
    def __init__(self, template_name, click=False, Opposite=False):
        self.template_path = f'/Users/yanzhang/Documents/python_code/Resource/{template_name}'
        self.template = self.load_template()
        self.click = click
        self.Opposite = Opposite

    def load_template(self):
        # 在初始化时加载模板图片
        template = cv2.imread(self.template_path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {self.template_path}")
        return template

    def capture_screen(self):
        # 使用PIL的ImageGrab直接截取屏幕
        screenshot = ImageGrab.grab()
        # 将截图对象转换为OpenCV格式
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return screenshot

    def find_image_on_screen(self, threshold=0.9):
        screen = self.capture_screen()
        result = cv2.matchTemplate(screen, self.template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 释放截图和模板图像以节省内存
        del screen
        if max_val >= threshold:
            return max_loc, self.template.shape
        else:
            return None, None

    def run1(self):
        found = False
        timeout = time.time() + 60
        while not found and time.time() < timeout:
            location, shape = self.find_image_on_screen()
            if location:
                if self.click:
                    # 计算中心坐标
                    center_x = (location[0] + shape[1] // 2) // 2
                    center_y = (location[1] + shape[0] // 2) // 2
                    
                    # 鼠标点击中心坐标
                    pyautogui.click(center_x, center_y)
                found = True
                print(f"找到图片位置: {location}")
            else:
                print("未找到图片，继续监控...")
                sleep(1)
        
        if time.time() > timeout:
            print("在60秒内未找到图片，退出程序。")
            webbrowser.open('file://' + os.path.realpath(txt_file_path), new=2)
    
    def run2(self):
        found = True
        while found:
            location, shape = self.find_image_on_screen()
            if location:
                pyautogui.scroll(-120)
                print(f"找到图片位置: {location}")
                sleep(1)
            else:
                print("未找到图片，继续监控...")
                found = False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python a.py <image_name> <click> <Opposite>")
        sys.exit(1)
    image_name = sys.argv[1]
    click = sys.argv[2].lower() == 'true'
    Opposite = sys.argv[3].lower() == 'true'
    detector = ScreenDetector(image_name, click, Opposite)
    if Opposite:
        detector.run2()
    else:
        detector.run1()
    