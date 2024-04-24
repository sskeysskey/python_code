import os
import cv2
import time
import pyperclip
import pyautogui
import subprocess
import numpy as np
from time import sleep
from PIL import ImageGrab
import sys
sys.path.append('/Users/yanzhang/Documents/python_code/Modules')
from Rename_segment import rename_first_segment_file

def capture_screen():
    # 使用PIL的ImageGrab直接截取屏幕
    screenshot = ImageGrab.grab()
    # 将截图对象转换为OpenCV格式
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return screenshot

# 查找图片
def find_image_on_screen(template, threshold=0.9):
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
    # 定义模板路径字典
    template_paths = {
        "kimi": "/Users/yanzhang/Documents/python_code/Resource/Kimi_copy.png",
        "mistral": "/Users/yanzhang/Documents/python_code/Resource/Mistral_copy.png",
        "thumb": "/Users/yanzhang/Documents/python_code/Resource/poe_thumb.png",
        "success": "/Users/yanzhang/Documents/python_code/Resource/poe_copy_success.png",
        "copy": "/Users/yanzhang/Documents/python_code/Resource/poe_copy.png"
    }

    # 读取所有模板图片，并存储在字典中
    templates = {}
    for key, path in template_paths.items():
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {path}")
        templates[key] = template

    pyautogui.click(x=560, y=571)
    sleep(0.5)
    pyautogui.scroll(-80)
    found_copy = False
    while not found_copy:
        location, shape = find_image_on_screen(templates["mistral"])
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
            location, shape = find_image_on_screen(templates["kimi"])
            if location:
                print("找到copy图了，准备点击copy...")
                # 计算中心坐标
                center_x = (location[0] + shape[1] // 2) // 2
                center_y = (location[1] + shape[0] // 2) // 2
                
                modify_x = center_x
                modify_y = center_y - 2

                # 鼠标点击中心坐标
                pyautogui.click(modify_x, modify_y)
                found_copy = True
            else:
                location, shape = find_image_on_screen(templates["thumb"])
                if location:
                    print("找到copy图了，准备点击copy...")
                    # 计算中心坐标
                    center_x = (location[0] + shape[1] // 2) // 2
                    center_y = (location[1] + shape[0] // 2) // 2
                    
                    xCoord = center_x
                    yCoord = center_y - 50

                    # 使用pyautogui移动鼠标并进行右键点击
                    pyautogui.moveTo(xCoord, yCoord)
                    pyautogui.click(button='right')
                    
                    sleep(1)
                    location, shape = find_image_on_screen(templates["copy"])
                    if location:
                        # 计算中心坐标
                        center_x = (location[0] + shape[1] // 2) // 2
                        center_y = (location[1] + shape[0] // 2) // 2
                        
                        # 鼠标点击中心坐标
                        pyautogui.click(center_x, center_y)
                    found_copy = True

                # 设置寻找poe_copy_success.png图片的超时时间为15秒
                sleep(1)
                found_success_image = False
                timeout_success = time.time() + 5
                while not found_success_image and time.time() < timeout_success:
                    location, shape = find_image_on_screen(templates["success"])
                    if location:
                        print("找到poe_copy_success图片，继续执行程序...")
                        found_success_image = True
                    sleep(1)  # 每次检测间隔1秒

    if not found_success_image:
        print("在15秒内未找到poe_copy_success图片，退出程序。")
        webbrowser.open('file://' + os.path.realpath(txt_file_path), new=2)

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
        non_empty_lines = [line.replace('#', '').replace('*', '').strip() for line in lines if line.strip()]
    else:
        print("剪贴板中没有内容或pyperclip无法访问剪贴板。")
        non_empty_lines = []  # 确保non_empty_lines是一个列表，即使剪贴板为空

    # 将非空行合并为一个字符串，用换行符分隔
    modified_content = '\n'.join(non_empty_lines)

    # 读取/tmp/segment.txt文件内容
    segment_file_path = '/tmp/segment.txt'
    segment_content = ""
    if os.path.exists(segment_file_path):
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

    # 使用函数
    directory = "/Users/yanzhang/Downloads/backup/TXT/Segments/"
    rename_first_segment_file(directory)

    # 检查并删除/tmp/segment.txt文件
    try:
        if os.path.exists(segment_file_path):
            os.remove(segment_file_path)
    except Exception as e:
        print(f"无法删除文件：{e}")

    book_auto_signal_path = "/private/tmp/book_auto_signal.txt"
    # 检查并删除/private/tmp/book_auto_signal.txt文件
    if os.path.exists(book_auto_signal_path):
        os.remove(book_auto_signal_path)

if __name__ == '__main__':
    main()