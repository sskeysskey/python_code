import cv2
import pyautogui
import numpy as np
from time import sleep

# 捕获屏幕
def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
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
    a_template_path = '/Users/yanzhang/Documents/python_code/Resource/poe_stop.png'  # A图片的实际路径
    b_template_path = '/Users/yanzhang/Documents/python_code/Resource/poe_more.png'  # B图片的实际路径
    
    # 持续寻找A图片
    while True:
        location, shape = find_image_on_screen(a_template_path)
        if location:
            print("找到A图片，继续监控...")
            sleep(2)  # 简短暂停再次监控
        else:
            print("A图片未找到，转而寻找B图片...")
            break  # A图片不再出现时，跳出循环，开始寻找B图片
    
    # 寻找B图片
    while True:
        location, shape = find_image_on_screen(b_template_path)
        if location:
            print("找到B图片，执行点击和移动操作...")
            # 计算中心坐标
            center_x = location[0] + shape[1] // 2
            center_y = location[1] + shape[0] // 2
            # 鼠标点击中心坐标
            pyautogui.click(center_x, center_y)
            # 如果需要移动鼠标并执行其他操作，可在此添加代码
            # ...
            break  # 执行完毕后退出B图片的循环
        else:
            print("未找到B图片，继续监控...")
            sleep(1)  # 没找到B图片，短暂休息后继续寻找

    print("程序执行完毕，退出。")

if __name__ == '__main__':
    main()