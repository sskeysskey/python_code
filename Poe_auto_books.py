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
    template_path_stop = '/Users/yanzhang/Documents/python_code/Resource/poe_stop.png'
    template_path_waiting = '/Users/yanzhang/Documents/python_code/Resource/poe_stillwaiting.png'
    template_path_success = '/Users/yanzhang/Documents/python_code/Resource/copy_success.png'
    template_path_thumb = '/Users/yanzhang/Documents/python_code/Resource/poe_thumb.png'
    template_path_failure = '/Users/yanzhang/Documents/python_code/Resource/poe_failure.png'
    template_path_no = '/Users/yanzhang/Documents/python_code/Resource/poe_no.png'

    found = False
    timeout_stop = time.time() + 15
    while not found and time.time() < timeout_stop:
        location, shape = find_image_on_screen(template_path_stop)
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
        location, shape = find_image_on_screen(template_path_stop)
        if location:
            print("找到poe_stop图片，继续监控...")
            pyautogui.scroll(-120)
            # 检测poe_stillwaiting.png图片
            location, shape = find_image_on_screen(template_path_waiting)
            if location:
                print("找到poe_stillwaiting图片，执行页面刷新操作...")
                pyautogui.click(x=617, y=574)
                sleep(0.5)
                pyautogui.hotkey('command', 'r')
            sleep(1)  # 简短暂停再次监控
        else:
            print("Stop图片没有了...")
            found_stop = False

    sleep(4)
    pyautogui.scroll(-80)
    found_thumb = False
    timeout_thumb = time.time() + 20
    while not found_thumb and time.time() < timeout_thumb:
        location, shape = find_image_on_screen(template_path_thumb)
        if location:
            sleep(3)
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2

            # 调整坐标，假设你已经计算好了需要传递给AppleScript的坐标值
            xCoord = center_x
            yCoord = center_y - 100

            found_thumb = True
            print(f"找到图片位置: {location}")
        else:
            print("未找到图片，继续监控...")
            pyautogui.scroll(-120)
            location, shape = find_image_on_screen(template_path_failure)
            if location:
                print("找到poe_failure图片，执行页面刷新操作...")
                sys.exit()
            location, shape = find_image_on_screen(template_path_no)
            if location:
                print("找到poe_no图片，执行页面刷新操作...")
                pyautogui.click(x=617, y=574)
                sleep(0.5)
                pyautogui.hotkey('command', 'r')
    
    if time.time() > timeout_thumb:
        print("在20秒内未找到图片，退出程序。")
        sys.exit()
    
    script_path = '/Users/yanzhang/Documents/ScriptEditor/click_copy_book.scpt'
    try:
        # 将坐标值作为参数传递给AppleScript
        process = subprocess.run(['osascript', script_path, str(xCoord), str(yCoord)], check=True, text=True, stdout=subprocess.PIPE)
        # 输出AppleScript的返回结果
        print(process.stdout.strip())
    except subprocess.CalledProcessError as e:
        # 如果有错误发生，打印错误信息
        print(f"Error running AppleScript: {e}")

    # 设置寻找copy_success.png图片的超时时间为15秒
    timeout_success = time.time() + 15
    found_success_image = False
    while not found_success_image and time.time() < timeout_success:
        location, shape = find_image_on_screen(template_path_success)
        if location:
            print("找到copy_success图片，继续执行程序...")
            found_success_image = True
        sleep(1)  # 每次检测间隔1秒

    if not found_success_image:
        print("在15秒内未找到copy_success图片，退出程序。")
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
        # 计算剪贴板内容中的中文字符数目
        chinese_characters_count = len(re.findall(r'[\u4e00-\u9fff]+', clipboard_content))

        # 检查是否同时包含"色情"和"露骨"关键字
        if "露骨" in clipboard_content and chinese_characters_count < 250:
            print("剪贴板内容不符合要求，程序终止执行。")
            # 内容非法后的过渡传递参数
            pyperclip.copy("illegal")
            exit()

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