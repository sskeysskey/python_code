import re
import os
import cv2
import sys
import pyperclip
import pyautogui
from time import sleep
from datetime import datetime

def capture_screen():
    # 定义截图路径
    screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
    # 使用pyautogui截图并直接保存
    pyautogui.screenshot(screenshot_path)
    # 读取刚才保存的截图文件
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    # 确保screenshot已经正确加载
    if screenshot is None:
        raise FileNotFoundError(f"截图未能正确保存或读取于路径 {screenshot_path}")
    # 返回读取的截图数据
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

# 检查 soldout.png 是否存在于屏幕上
def check_soldout_image():
    remaining_template_path = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout1.png'  # 替换为你的remaining.png图片实际路径
    location, shape = find_image_on_screen(remaining_template_path, threshold=0.9)
    return bool(location)

# 主函数
def main():
    try:
        template_path1 = '/Users/yanzhang/Documents/python_code/Resource/claude_done_125.png'
        template_path2 = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout2.png'
        sleep(2)

        location, shape = find_image_on_screen(template_path2)
        if location:
                # 设置stop_signal文件的保存目录
                stop_signal_directory = '/private/tmp'
                
                # 设置stop_signal文件的保存路径
                now = datetime.now()
                time_str = now.strftime("_%m_%d_%H")
                stop_signal_file_name = f"stop_signal{time_str}.txt"
                stop_signal_path = os.path.join(stop_signal_directory, stop_signal_file_name)

                with open(stop_signal_path, 'w') as signal_file:
                        signal_file.write('stop')
                sys.exit(0)  # 安全退出程序
        else:
                print("没找到图片，继续执行...")

        while True:
            location, shape = find_image_on_screen(template_path1)
            if location:
                # 计算中心坐标
                center_x = (location[0] + shape[1] // 2) // 2
                center_y = (location[1] + shape[0] // 2) // 2
                
                # 鼠标点击中心坐标
                pyautogui.click(center_x, center_y)

                # 读取剪贴板内容
                clipboard_content = pyperclip.paste()

                # 使用splitlines()分割剪贴板内容为多行
                lines = clipboard_content.splitlines()
                # 移除空行
                non_empty_lines = [line for line in lines if line.strip()]

                # 判断第一句是否以“首先”或“第一”开头
                first_sentence_start_with_special = non_empty_lines and \
                    (non_empty_lines[0].startswith('首先') or non_empty_lines[0].startswith('第一'))

                # 计算非空行中以数字或符号开头的行数
                num_start_with_digit_symbol_or_chinese_char = sum(bool(re.match(r'^[\d\W]|^第', line)) for line in non_empty_lines)

                # 判断是否超过50%
                if num_start_with_digit_symbol_or_chinese_char >= len(non_empty_lines) / 2:
                    # 判断最后一行是否以数字或“第”字开头
                    if not non_empty_lines[-1].startswith(('第',)) and not re.match(r'^\d', non_empty_lines[-1]):
                        # 如果不是，则剪贴板中第一行和最后一句都删除
                        modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):-1])
                    else:
                        # 如果是，则只删除第一行
                        modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])
                else:
                    # 如果不足50%，则只删除第一句（除非第一句以“首先”或“第一”开头）
                    modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])

                # 读取/tmp/segment.txt文件内容
                segment_file_path = '/tmp/segment.txt'
                with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
                    segment_content = segment_file.read()

                # 在segment_content后面添加一个换行符
                segment_content += '\n'
                
                # 将读取到的segment_content内容插入在剪贴板内容的最前面
                final_content = segment_content + modified_content

                # 设置txt文件的保存目录
                txt_directory = '/Users/yanzhang/Documents/News'
                
                # 设置TXT文件的保存路径
                now = datetime.now()
                time_str = now.strftime("_%y_%m_%d")
                txt_file_name = f"News{time_str}.txt"
                txt_file_path = os.path.join(txt_directory, txt_file_name)

                if not os.path.isfile(txt_file_path):
                    with open(txt_file_path, 'w', encoding='utf-8-sig') as txt_file:
                        pass  # 创建文件后不进行任何操作，文件会被关闭

                # 追加处理后的内容到TXT文件
                with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
                    txt_file.write(final_content)
                    txt_file.write('\n\n')  # 添加两个换行符以创建一个空行

                sleep(1)

                # 设置stop_signal文件的保存目录
                stop_signal_directory = '/private/tmp'
                
                # 设置stop_signal文件的保存路径
                now = datetime.now()
                time_str = now.strftime("_%m_%d_%H")
                stop_signal_file_name = f"stop_signal{time_str}.txt"
                stop_signal_path = os.path.join(stop_signal_directory, stop_signal_file_name)

                # 检查 soldout.png 是否存在于屏幕上
                if check_soldout_image():
                    # 如果存在，则写文件
                    with open(stop_signal_path, 'w') as signal_file:
                        signal_file.write('stop')
                    break
                else:
                    # 如果soldout.png不存在，则按原步骤执行
                    break
                
            else:
                print("未找到A图片，继续监控...")
                sleep(1)  # 简短暂停再次监控
    
    finally:
        screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print("截图文件已删除。")

if __name__ == '__main__':
    main()