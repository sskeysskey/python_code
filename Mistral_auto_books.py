import re
import os
import cv2
import time
import pyperclip
import pyautogui
import subprocess
import numpy as np
from time import sleep
from PIL import ImageGrab

def capture_screen():
    # 使用PIL的ImageGrab直接截取屏幕
    screenshot = ImageGrab.grab()
    # 将截图对象转换为OpenCV格式
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
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

# 主函数
def main():
    template_stop = '/Users/yanzhang/Documents/python_code/Resource/Mistral_stop.png'
    template_copy = '/Users/yanzhang/Documents/python_code/Resource/Mistral_copy.png'

    found = False
    timeout_stop = time.time() + 15
    while not found and time.time() < timeout_stop:
        location, shape = find_image_on_screen(template_stop)
        if location:
            found = True
            print(f"找到图片位置: {location}")
        else:
            print("未找到图片，继续监控...")
            sleep(1)

    if time.time() > timeout_stop:
        print("在15秒内未找到thumb图片，退出程序。")
        sys.exit()

    found_stop = True
    while found_stop:
        location, shape = find_image_on_screen(template_stop)
        if location:
            print("找到stop图了，准备下一步...")
            pyautogui.scroll(-80)
            sleep(1) # 继续监控
        else:
            print("没找到图片，继续执行...")
            found_stop = False

    found_copy = False
    timeout_copy = time.time() + 5
    while not found_copy and time.time() < timeout_copy:
        location, shape = find_image_on_screen(template_copy)
        if location:
            print("找到copy图了，准备点击copy...")
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2
            
            # 鼠标点击中心坐标
            pyautogui.click(center_x, center_y)
            found_copy = True
        else:
            print("没找到图片，继续执行...")
            pyautogui.scroll(-120)
            sleep(1)

    if not found_copy:
        print("在5秒内未找到copy_success图片，退出程序。")
        sys.exit()

    # 设置目录路径
    directory_path = '/Users/yanzhang/Documents/'

    # 寻找目录下的第一个txt文件
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            txt_file_path = os.path.join(directory_path, filename)
            break  # 找到第一个txt文件后停止循环

    # 读取剪贴板内容
    clipboard_content = pyperclip.paste()

    # 检查clipboard_content是否为None或者是否是一个字符串
    if clipboard_content:
        # 使用splitlines()分割剪贴板内容为多行
        lines = clipboard_content.splitlines()
        # 移除空行
        non_empty_lines = [line for line in lines if line.strip()]
    else:
        print("剪贴板中没有内容或pyperclip无法访问剪贴板。")
        non_empty_lines = []  # 确保non_empty_lines是一个列表，即使剪贴板为空

    # 将非空行合并为一个字符串，用换行符分隔
    modified_content = '\n'.join(non_empty_lines)

    # 读取/tmp/segment.txt文件内容
    segment_file_path = '/tmp/segment.txt'
    with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
        segment_content = segment_file.read().strip()  # 使用strip()移除可能的空白字符

    # 在segment_content后面添加一个换行符
    segment_content += '\n'
    
    # 将读取到的segment_content内容插入在剪贴板内容的最前面
    final_content = segment_content + modified_content

    # 追加处理后的内容到TXT文件
    with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
        txt_file.write(final_content)
        txt_file.write('\n\n')  # 添加两个换行符以创建一个空行

if __name__ == '__main__':
    main()