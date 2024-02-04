import re
import os
import cv2
import pyperclip
import pyautogui
from time import sleep
from datetime import datetime, timedelta

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

def append_to_html(html_file_path, segment_content, modified_content):
    # 追加内容到HTML文件
    with open(html_file_path, 'a', encoding='utf-8-sig') as html_file:
        html_file.write(f"""
            <tr>
                <td>{segment_content}</td>
                <td>{modified_content}</td>
            </tr>
        """)

def create_html_skeleton(html_file_path):
    # 创建HTML框架
    with open(html_file_path, 'w', encoding='utf-8-sig') as html_file:
        html_file.write("""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>新闻摘要</title>
        </head>
        <body>
            <table border="1">
                <tr>
                    <th>来源</th>
                    <th>摘要</th>
                </tr>
        """)

def close_html_skeleton(html_file_path):
    # 结束HTML框架
    with open(html_file_path, 'a', encoding='utf-8-sig') as html_file:
        html_file.write("""
            </table>
        </body>
        </html>
        """)

# 主函数
def main():
                pyautogui.click(button='right')
                sleep(0.5)
                # 移动鼠标并再次点击
                pyautogui.moveRel(110, 118)  # 往右移动110，往下移动118
                sleep(0.5)
                pyautogui.click()  # 执行点击操作
                sleep(1)

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
                if num_start_with_digit_symbol_or_chinese_char > len(non_empty_lines) / 2:
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

                # 设置txt文件的保存目录
                txt_directory = '/Users/yanzhang/Documents/News'
                
                # 追加处理后的内容到HTML文件
                now = datetime.now()
                time_str = now.strftime("_%y_%m_%d")
                html_file_name = f"News{time_str}.html"
                html_file_path = os.path.join(txt_directory, html_file_name)

                # 检查HTML文件是否已经存在
                if not os.path.isfile(html_file_path):
                    # 创建HTML框架
                    create_html_skeleton(html_file_path)

                # 追加内容到HTML文件
                append_to_html(html_file_path, segment_content, modified_content)

                if not os.path.isfile(html_file_path):
                    close_html_skeleton(html_file_path)
                

if __name__ == '__main__':
    main()