import os
import cv2
import time
import datetime
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
            yCoord = center_y - 130

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
        print("在20秒内未找到thumb图片，退出程序。")
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

    # 获取当前日期并格式化为指定的文件名形式
    current_date = datetime.datetime.now().strftime('%m月%d日.srt')

    # 拼接文件完整路径
    file_path = os.path.join('/Users/yanzhang/Movies', current_date)

    # 读取剪贴板内容
    clipboard_content = pyperclip.paste()

    # 使用正则表达式找到第一个以数字开头并且紧跟一个换行符的行
    match = re.search(r'^(\d+).*\n', clipboard_content, re.MULTILINE)

    if match:
        start_index = match.start()  # 获取匹配行的起始索引
        number_at_start = int(match.group(1))  # 获取行首的数字
        remaining_content = clipboard_content[start_index:]  # 截取剩余内容

        # 根据行首数字决定是创建新文件还是追加现有文件
        if number_at_start == 1 or not os.path.exists(file_path):
            mode = 'w'  # 创建新文件
        else:
            mode = 'a'  # 追加到现有文件

        # 写入文件
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(remaining_content)
            file.write('\n\n')  # 添加两个换行符以创建一个空行
        print('内容处理完成，已经写入到', file_path)
    else:
        print('剪贴板内容中没有找到符合条件的行。')

if __name__ == '__main__':
    main()