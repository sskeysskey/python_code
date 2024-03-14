import re
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
    while True:
        location, shape = find_image_on_screen(template_path_stop)
        if location:
            print("找到poe_stop图片，继续监控...")
            # 检测poe_stillwaiting.png图片
            location, shape = find_image_on_screen(template_path_waiting)
            if location:
                print("找到poe_stillwaiting图片，执行页面刷新操作...")
                pyautogui.click(x=617, y=574)
                sleep(1)
                pyautogui.hotkey('command', 'r')
            sleep(3)  # 简短暂停再次监控
        else:
            script_path = '/Users/yanzhang/Documents/ScriptEditor/click_copy_book.scpt'
            try:
                # 运行AppleScript文件
                process = subprocess.run(['osascript', script_path], check=True, text=True, stdout=subprocess.PIPE)
                # 输出AppleScript的返回结果
                print(process.stdout.strip())
            except subprocess.CalledProcessError as e:
                # 如果有错误发生，打印错误信息
                print(f"Error running AppleScript: {e}")

            # 设置寻找copy_success.png图片的超时时间为5秒
            timeout = time.time() + 5
            found_success_image = False
            while not found_success_image and time.time() < timeout:
                location, shape = find_image_on_screen(template_path_success)
                if location:
                    print("找到copy_success图片，继续执行程序...")
                    found_success_image = True
                time.sleep(1)  # 每次检测间隔1秒

            if not found_success_image:
                print("在5秒内未找到copy_success图片，退出程序。")
                sys.exit()

            # 设置TXT文件的保存路径
            txt_file_path = '/Users/yanzhang/Documents/book.txt'

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
            break  # 图片消失后退出循环

if __name__ == '__main__':
    main()