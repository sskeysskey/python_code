# o1优化后代码

import cv2
import time
import argparse
import pyautogui
import subprocess
import numpy as np
import sys
from PIL import ImageGrab

# 固定点击坐标与滚动值，可根据需要自行调整
SCREEN_CLICK_COORDS = (591, 574)
SCROLL_AMOUNT = -80
SCROLL_AMOUNT_LARGE = -120
SECONDARY_CLICK_COORDS = (618, 458)


def capture_screen():
    """
    使用PIL的ImageGrab直接截取屏幕，并转换为OpenCV格式
    """
    screenshot = ImageGrab.grab()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def find_image_on_screen(template, threshold=0.9):
    """
    在当前屏幕中查找给定模板图像的匹配位置（精度默认0.9）。
    如果找到，则返回 (top_left坐标, 模板形状)，否则返回 (None, None)。
    """
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    # 释放截图及相关资源
    del screen
    if max_val >= threshold:
        return max_loc, template.shape
    return None, None


def refresh_page():
    """
    对当前页面执行 AppleScript 刷新操作
    """
    script = """
    tell application "System Events"
        key code 15 using command down
    end tell
    """
    subprocess.run(['osascript', '-e', script], check=True)
    # 给系统一点时间来完成操作
    time.sleep(0.5)


def click_retry_and_refresh():
    """
    找到retry图片后，点击固定坐标并执行页面刷新
    """
    print("找到poe_retry图片，执行页面刷新操作...")
    pyautogui.click(*SCREEN_CLICK_COORDS)
    time.sleep(0.5)
    refresh_page()


def main(mode):
    # 定义模板路径字典
    template_paths = {
        "stop": "/Users/yanzhang/Documents/python_code/Resource/poe_stop.png",
        "success": "/Users/yanzhang/Documents/python_code/Resource/poe_copy_success.png",
        "thumb": "/Users/yanzhang/Documents/python_code/Resource/poe_thumb.png",
        "compare": "/Users/yanzhang/Documents/python_code/Resource/poe_compare.png",
        "copy": "/Users/yanzhang/Documents/python_code/Resource/poe_copy.png",
        "retry": "/Users/yanzhang/Documents/python_code/Resource/poe_retry.png",
    }

    # 读取所有模板图片，并存储在字典中
    templates = {}
    for key, path in template_paths.items():
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {path}")
        templates[key] = template

    # 第一阶段：在 10 秒内尝试找到 stop 图片
    found_stop_image = False
    timeout_stop = time.time() + 10
    while not found_stop_image and time.time() < timeout_stop:
        location, shape = find_image_on_screen(templates["stop"])
        if location:
            print(f"找到图片位置: {location}")
            pyautogui.moveTo(*SCREEN_CLICK_COORDS)
            found_stop_image = True
        else:
            print("未找到stop图片，继续监控...")
            pyautogui.moveTo(*SCREEN_CLICK_COORDS)
            pyautogui.scroll(SCROLL_AMOUNT)
            time.sleep(1)

    # 第二阶段：一直检测“stop图片是否还在”，如果在则尝试找“retry”图片并刷新
    monitoring_stop = True
    while monitoring_stop:
        location, shape = find_image_on_screen(templates["stop"])
        if location:
            print("找到poe_stop图片，继续监控...")
            pyautogui.scroll(SCROLL_AMOUNT_LARGE)
            location_retry, shape_retry = find_image_on_screen(templates["retry"])
            if location_retry:
                click_retry_and_refresh()
        else:
            print("Stop图片没有了...")
            monitoring_stop = False

    # 如果模式是 long
    if mode == 'long':
        found_thumb = False
        timeout_thumb = time.time() + 35
        while not found_thumb and time.time() < timeout_thumb:
            location, shape = find_image_on_screen(templates["thumb"])
            if location:
                found_thumb = True
                print(f"找到图片位置: {location}")
            else:
                print("未找到thumb图片，继续监控...")
                pyautogui.scroll(SCROLL_AMOUNT)
                # 如果retry出现则刷新
                # location_retry, shape_retry = find_image_on_screen(templates["retry"])
                # if location_retry:
                #     click_retry_and_refresh()
                time.sleep(1)

        if time.time() > timeout_thumb:
            print("在35秒内未找到thumb图片，退出程序。")
            sys.exit()

        # 找 compare 图片
        found_compare = False
        timeout_compare = time.time() + 25
        while not found_compare and time.time() < timeout_compare:
            location_compare, shape_compare = find_image_on_screen(templates["compare"])
            if location_compare:
                found_compare = True
            else:
                pyautogui.click(*SECONDARY_CLICK_COORDS)
                pyautogui.scroll(SCROLL_AMOUNT)
                print("未找到compare图片，继续监控...")

        # 找 thumb，然后右键点击
        location, shape = find_image_on_screen(templates["thumb"])
        if location:
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2
            xCoord = center_x
            yCoord = center_y - 200
            pyautogui.moveTo(xCoord, yCoord)
            pyautogui.click(button='right')
        else:
            print(f"找不到thumb图片，location结果: {location}")

    elif mode == 'short':
        # 如果模式是 short
        found_thumb = False
        timeout_thumb = time.time() + 25
        while not found_thumb and time.time() < timeout_thumb:
            location, shape = find_image_on_screen(templates["thumb"])
            if location:
                center_x = (location[0] + shape[1] // 2) // 2
                center_y = (location[1] + shape[0] // 2) // 2
                xCoord = center_x
                yCoord = center_y - 100
                pyautogui.moveTo(xCoord, yCoord)
                pyautogui.click(button='right')
                found_thumb = True
            else:
                print(f"找到thumb图片位置: {location}")
                pyautogui.scroll(SCROLL_AMOUNT)
                # location_retry, shape_retry = find_image_on_screen(templates["retry"])
                # if location_retry:
                #     click_retry_and_refresh()
                time.sleep(0.5)

    # 找 copy 图片，点击它
    time.sleep(0.5)
    found_copy = False
    timeout_copy = time.time() + 25
    while not found_copy and time.time() < timeout_copy:
        location_copy, shape_copy = find_image_on_screen(templates["copy"])
        if location_copy:
            center_x = (location_copy[0] + shape_copy[1] // 2) // 2
            center_y = (location_copy[1] + shape_copy[0] // 2) // 2
            pyautogui.click(center_x, center_y)
            found_copy = True
            print(f"找到copy图片位置: {location_copy}")
        else:
            print("未找到copy图片，继续监控...")
            time.sleep(1)

    # 最后找 success 图片
    time.sleep(1)
    found_success_image = False
    timeout_success = time.time() + 25
    while not found_success_image and time.time() < timeout_success:
        location_success, shape_success = find_image_on_screen(templates["success"])
        if location_success:
            print("找到poe_copy_success图片，继续执行程序...")
            found_success_image = True
        else:
            time.sleep(1)  # 每次检测间隔1秒


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files based on the given mode.')
    parser.add_argument('mode', choices=['short', 'long'], help='The processing mode: short or long')
    args = parser.parse_args()

    main(args.mode)