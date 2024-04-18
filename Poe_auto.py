import cv2
import time
import pyautogui
import subprocess
import numpy as np
from time import sleep
from PIL import ImageGrab

# 截取屏幕
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
    template_path_success = '/Users/yanzhang/Documents/python_code/Resource/poe_copy_success.png'
    template_path_thumb = '/Users/yanzhang/Documents/python_code/Resource/poe_thumb.png'
    template_path_failure = '/Users/yanzhang/Documents/python_code/Resource/poe_failure.png'
    template_path_no = '/Users/yanzhang/Documents/python_code/Resource/poe_no.png'
    template_path_compare = '/Users/yanzhang/Documents/python_code/Resource/poe_compare.png'

    found = False
    timeout_stop = time.time() + 15
    while not found and time.time() < timeout_stop:
        location, shape = find_image_on_screen(template_path_stop)
        if location:
            found = True
            print(f"找到图片位置: {location}")
        else:
            print("未找到图片，继续监控...")
            pyautogui.scroll(-80)
            location, shape = find_image_on_screen(template_path_failure)
            if location:
                print("找到poe_failure图片，执行页面刷新操作...")
                pyautogui.click(x=617, y=574)
                sleep(0.5)
                pyautogui.hotkey('command', 'r')
            location, shape = find_image_on_screen(template_path_no)
            if location:
                print("找到poe_no图片，执行页面刷新操作...")
                pyautogui.click(x=617, y=574)
                sleep(0.5)
                pyautogui.hotkey('command', 'r')
            sleep(1)

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

    found = False
    timeout_compare = time.time() + 25
    while not found and time.time() < timeout_compare:
        location, shape = find_image_on_screen(template_path_compare)
        if location:
            found = True
            print(f"找到图片位置: {location}")
        else:
            print("未找到图片，继续监控...")
            pyautogui.scroll(-80)
            sleep(1)

    if time.time() > timeout_compare:
        print("在15秒内未找到图片，退出程序。")
        sys.exit()

    pyautogui.scroll(-80)
    found_thumb = False
    timeout_thumb = time.time() + 10
    while not found_thumb and time.time() < timeout_thumb:
        location, shape = find_image_on_screen(template_path_thumb)
        if location:
            sleep(1)
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2

            # 调整坐标，假设你已经计算好了需要传递给AppleScript的坐标值
            xCoord = center_x
            xFix = center_x - 50
            yCoord = center_y - 100

            found_thumb = True
            print(f"找到图片位置: {location}")
        else:
            print("未找到图片，继续监控...")
            pyautogui.scroll(-80)
            sleep(1)

    if time.time() > timeout_thumb:
        print("在20秒内未找到图片，退出程序。")
        sys.exit()

    script_path = '/Users/yanzhang/Documents/ScriptEditor/Click_copy.scpt'
    try:
        # 将坐标值作为参数传递给AppleScript
        process = subprocess.run(['osascript', script_path, str(xCoord), str(yCoord)], check=True, text=True, stdout=subprocess.PIPE)
        # 输出AppleScript的返回结果
        print(process.stdout.strip())
    except subprocess.CalledProcessError as e:
        # 如果有错误发生，打印错误信息
        print(f"Error running AppleScript: {e}")

    # 设置寻找poe_copy_success.png图片的超时时间为15秒
    sleep(1)
    found_success_image = False
    timeout_success = time.time() + 15
    while not found_success_image and time.time() < timeout_success:
        location, shape = find_image_on_screen(template_path_success)
        if location:
            print("找到poe_copy_success图片，继续执行程序...")
            found_success_image = True
        else:
            # 移动到指定坐标
            pyautogui.moveTo(xFix, yCoord)
            # 点击左键
            pyautogui.click()
            try:
                # 将坐标值作为参数传递给AppleScript
                process = subprocess.run(['osascript', script_path, str(xCoord), str(yCoord)], check=True, text=True, stdout=subprocess.PIPE)
                # 输出AppleScript的返回结果
                print(process.stdout.strip())
            except subprocess.CalledProcessError as e:
                # 如果有错误发生，打印错误信息
                print(f"Error running AppleScript: {e}")
            sleep(1)  # 每次检测间隔1秒

    if not found_success_image:
        print("在15秒内未找到poe_copy_success图片，退出程序。")
        sys.exit()

if __name__ == '__main__':
    main()