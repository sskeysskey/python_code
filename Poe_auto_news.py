import re
import os
import cv2
import html
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

def append_to_html(html_file_path, segment_content, modified_content):
    # 获取当前的系统时间，并格式化为字符串
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # HTML转义段落和修改后的内容
    escaped_segment = html.escape(segment_content).replace('\n', '<br>\n')
    escaped_modified = html.escape(modified_content).replace('\n', '<br>\n')
    
    # 读取整个HTML文件内容
    with open(html_file_path, 'r', encoding='utf-8-sig') as html_file:
        html_content = html_file.read()

    # 构造新的表格行
    new_row = f"""
        <tr>
            <td>{current_time}</td>
            <td>{escaped_modified}</td>
        </tr>
    """

    # 找到插入点（在</tr>标签后的第一次出现的位置，这意味着在表格的开头）
    insert_position = html_content.find("</tr>") + 5

    # 插入新的表格行
    updated_html_content = html_content[:insert_position] + new_row + html_content[insert_position:]

    # 写回修改后的HTML内容
    with open(html_file_path, 'w', encoding='utf-8-sig') as html_file:
        html_file.write(updated_html_content)

def create_html_skeleton(html_file_path, title):
    # 创建HTML框架，并设定字体大小
    with open(html_file_path, 'w', encoding='utf-8-sig') as html_file:
        html_file.write(f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-size: 28px; /* 这里设置字体大小 */
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <table>
                <tr>
                    <th>时间</th>
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
    html_skeleton_created = False
    html_file_path = ''  # 用空字符串初始化
    try:
        template_path_stop = '/Users/yanzhang/Documents/python_code/Resource/poe_stop.png'
        template_path_waiting = '/Users/yanzhang/Documents/python_code/Resource/poe_stillwaiting.png'
        while True:
            location, shape = find_image_on_screen(template_path_stop)
            if location:
                print("找到poe_stop图片，继续监控...")
                # 检测poe_stillwaiting.png图片
                location, shape = find_image_on_screen(template_path_waiting)
                if location:
                    print("找到poe_stillwaiting图片，执行页面刷新操作...")
                    # 执行页面刷新（模拟Command + R）
                    pyautogui.click(x=635, y=493)
                    sleep(0.5)
                    pyautogui.hotkey('command', 'r')
                sleep(1)  # 简短暂停再次监控
            else:
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
                    segment_content = segment_file.read().strip()  # 使用strip()移除可能的空白字符

                # 确定segment内容，并选择相应的HTML文件
                segment_to_html_file = {
                    "technologyreview": "technologyreview.html",
                    "economist": "economist.html",
                    "wsj": "wsj.html",
                    "nytimes": "nytimes.html",
                    "ft": "FT.html",
                    "nikkei": "nikkei.html",
                }

                # 根据segment内容获取对应的HTML文件名
                html_file_name = segment_to_html_file.get(segment_content.lower(), "other.html")
                html_file_path = os.path.join('/Users/yanzhang/Documents/sskeysskey.github.io/news', html_file_name)

                # 根据segment内容获取对应的标题
                title = segment_content if segment_content.lower() in segment_to_html_file else "新闻摘要"

                # 检查HTML文件是否已经存在
                html_skeleton_created = os.path.isfile(html_file_path)

                # 检查HTML文件是否已经存在
                if not html_skeleton_created:
                    create_html_skeleton(html_file_path, title)
                
                # 追加内容到HTML文件
                append_to_html(html_file_path, segment_content, modified_content)
                break
                
    finally:
        # 最后，关闭HTML框架
        if html_skeleton_created and not os.path.isfile(html_file_path):
            close_html_skeleton(html_file_path)

        screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print("截图文件已删除。")

if __name__ == '__main__':
    main()