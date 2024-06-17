import os
import cv2
import time
import pyperclip
import pyautogui
import numpy as np
from time import sleep
from PIL import ImageGrab
import sys
sys.path.append('/Users/yanzhang/Documents/python_code/Modules')
from Rename_segment import rename_first_segment_file

def capture_screen():
    screenshot = ImageGrab.grab()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return screenshot

def find_image_on_screen(template, threshold=0.9):
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        return max_loc, template.shape
    return None, None

def click_image_center(location, shape, offset_x=0, offset_y=0):
    center_x = location[0] + shape[1] // 2 + offset_x
    center_y = location[1] + shape[0] // 2 + offset_y
    pyautogui.click(center_x, center_y)

def main():
    template_paths = {
        "kimi": "/Users/yanzhang/Documents/python_code/Resource/Kimi_copy.png",
        "mistral": "/Users/yanzhang/Documents/python_code/Resource/Mistral_copy.png",
        "thumb": "/Users/yanzhang/Documents/python_code/Resource/poe_thumb.png",
        "success": "/Users/yanzhang/Documents/python_code/Resource/poe_copy_success.png",
        "copy": "/Users/yanzhang/Documents/python_code/Resource/poe_copy.png"
    }

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
    found_success_image = False

    while not found_copy:
        for key in ["mistral", "kimi", "thumb"]:
            location, shape = find_image_on_screen(templates[key])
            if location:
                if key == "thumb":
                    pyautogui.moveTo(location[0] + shape[1] // 2, location[1] + shape[0] // 2 - 50)
                    pyautogui.click(button='right')
                    sleep(1)
                    location, shape = find_image_on_screen(templates["copy"])
                if location:
                    click_image_center(location, shape, offset_y=-2 if key == "kimi" else 0)
                    found_copy = True
                    break
        else:
            print("未找到图片，继续执行...")

        if found_copy:
            timeout_success = time.time() + 5
            while not found_success_image and time.time() < timeout_success:
                location, shape = find_image_on_screen(templates["success"])
                if location:
                    print("找到poe_copy_success图片，继续执行程序...")
                    found_success_image = True
                sleep(1)

    if not found_success_image:
        print("在5秒内未找到poe_copy_success图片，退出程序。")
        webbrowser.open('file://' + os.path.realpath(txt_file_path), new=2)

    directory_path = '/Users/yanzhang/Documents/'
    txt_file_path = next((os.path.join(directory_path, filename) for filename in os.listdir(directory_path) if filename.endswith('.txt')), None)

    clipboard_content = pyperclip.paste() or ""
    non_empty_lines = [line.replace('#', '').replace('*', '').strip() for line in clipboard_content.splitlines() if line.strip()]
    modified_content = '\n'.join(non_empty_lines)

    segment_file_path = '/tmp/segment.txt'
    segment_content = ""
    if os.path.exists(segment_file_path):
        with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
            segment_content = segment_file.read().strip()

    final_content = segment_content + '\n' + modified_content

    if txt_file_path:
        with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
            txt_file.write(final_content)
            txt_file.write('\n\n')

    directory = "/Users/yanzhang/Downloads/backup/TXT/Segments/"
    rename_first_segment_file(directory)

    try:
        if os.path.exists(segment_file_path):
            os.remove(segment_file_path)
    except Exception as e:
        print(f"无法删除文件：{e}")

    book_auto_signal_path = "/private/tmp/book_auto_signal.txt"
    if os.path.exists(book_auto_signal_path):
        os.remove(book_auto_signal_path)

if __name__ == '__main__':
    main()