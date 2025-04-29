import os
import cv2
import html
import time
import shutil
import glob
import sys
import pyperclip
import subprocess
import pyautogui
import numpy as np
from PIL import ImageGrab
from datetime import datetime

# 常量定义
TXT_DIRECTORY = '/Users/yanzhang/Documents/News'
HTML_DIRECTORY = '/Users/yanzhang/Documents/sskeysskey.github.io/news'
SCRIPT_PATH = '/Users/yanzhang/Documents/ScriptEditor/Close_Tab_News.scpt'
SEGMENT_FILE_PATH = '/tmp/segment.txt'
SITE_FILE_PATH = '/tmp/site.txt'

SEGMENT_TO_HTML_FILE = {
    "technologyreview": "technologyreview.html",
    "economist": "economist.html",
    "nytimes": "nytimes.html",
    "nikkei": "nikkei.html",
    "bloomberg": "bloomberg.html",
    "hbr": "hbr.html",
    "ft": "ft.html",
    "wsj": "wsj.html"
}

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

def get_clipboard_content():
    content = pyperclip.paste()
    
    if not content:  # 检查剪贴板是否为空
        return ""
    
    # 处理多行内容，去除空行和首尾空白
    return '\n'.join(line.strip() for line in content.splitlines() if line.strip())

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        return file.read().strip()

def write_html_skeleton(file_path, title):
    with open(file_path, 'w', encoding='utf-8-sig') as file:
        file.write(f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-size: 28px; }}
                table {{ width: 100%; border-collapse: collapse; border: 2px solid #000; box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2); }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 2px solid #000; border-right: 2px solid #000; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:hover {{ background-color: #f5f5f5; }}
                tr:last-child td {{ border-bottom: 2px solid #000; }}
                td:last-child, th:last-child {{ border-right: none; }}
            </style>
        </head>
        <body>
            <table>
                <tr>
                    <th>时间</th>
                    <th>摘要</th>
                </tr>
        """)

def append_to_html(file_path, current_time, content):
    with open(file_path, 'r+', encoding='utf-8-sig') as file:
        content = html.escape(content).replace('\n', '<br>\n')
        html_content = file.read()
        insert_position = html_content.find("</tr>") + 5
        new_row = f"""
            <tr>
                <td>{current_time}</td>
                <td>{content}</td>
            </tr>
        """
        updated_content = html_content[:insert_position] + new_row + html_content[insert_position:]
        file.seek(0)
        file.write(updated_content)

def close_html_skeleton(file_path):
    with open(file_path, 'a', encoding='utf-8-sig') as file:
        file.write("""
            </table>
        </body>
        </html>
        """)

def main():
    # 获取传入的URL参数
    url = sys.argv[1] if len(sys.argv) > 1 else "No URL provided"
    
    def move_and_record_images(url):
        """
        移动多种格式图片并记录到article_copier.txt
        """
        source_dir = "/Users/yanzhang/Downloads"
        today = datetime.now().strftime("%y%m%d")
        target_dir = f"/Users/yanzhang/Downloads/news_image_{today}"
        record_file = f"/Users/yanzhang/Documents/News/article_copier_{today}.txt"
        
        # 支持的图片格式
        image_formats = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.avif", "*.gif"]

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        os.makedirs(os.path.dirname(record_file), exist_ok=True)

        # 获取所有图片文件
        image_files = []
        for format in image_formats:
            image_files.extend(glob.glob(os.path.join(source_dir, format)))
        moved_files = []

        # 移动文件
        for image_file in image_files:
            filename = os.path.basename(image_file)
            target_path = os.path.join(target_dir, filename)
            shutil.move(image_file, target_path)
            moved_files.append(filename)

        # 写入记录文件，无论是否有移动文件都写入URL
        content = f"{url}\n\n"
        if moved_files:
            content += "\n".join(moved_files) + "\n\n"
        
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    template_paths = {
        "copy": "/Users/yanzhang/Documents/python_code/Resource/Kimi_copy.png",
        "outofline": "/Users/yanzhang/Documents/python_code/Resource/Kimi_outofline.png"
    }

    # 读取所有模板图片，并存储在字典中
    templates = {}
    for key, path in template_paths.items():
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {path}")
        templates[key] = template

    timeout = time.time() + 60  # 60 秒后超时
    found = False
    while time.time() < timeout and not found:
        # 1) 尝试找 outofline
        loc_out, shape_out = find_image_on_screen(templates["outofline"])
        if loc_out:
            print(f"找到 outofline 图片位置: {loc_out}")
            found = True
            break

        # 2) 再尝试找 copy
        loc_cp, shape_cp = find_image_on_screen(templates["copy"])
        if loc_cp:
            print("找到 copy 图，准备点击 copy...")
            time.sleep(1.5)
            loc_cp, shape_cp = find_image_on_screen(templates["copy"])
            if loc_cp:
                # 计算图片中心
                center_x = (loc_cp[0] + shape_cp[1] // 2) // 2
                center_y = (loc_cp[1] + shape_cp[0] // 2) // 2

                # 如果想在中心稍微偏移几像素：
                center_y -= 2

                pyautogui.click(center_x, center_y)
                found = True
                break

        # 3) 两张都没找到，滚一点、等一点，然后再试
        pyautogui.scroll(-80)
        time.sleep(0.5)

    if not found:
        print("60秒内未找到 outofline 或 copy 图片，退出或执行兜底逻辑。")

    # 跳转到clipboard_content处理部分
    clipboard_content = get_clipboard_content()
    segment_content = read_file(SEGMENT_FILE_PATH)
    site_content = read_file(SITE_FILE_PATH)
    # site_content_with_tags = f'<document>{site_content}</document>请用中文详细总结这篇文章'
    site_content_with_tags = f'{site_content}'
    
    # final_content = f"{segment_content}\n{site_content_with_tags}\n\n{clipboard_content}"
    final_content = f"{site_content_with_tags}\n\n{clipboard_content}"
    
    now = datetime.now()
    txt_file_name = f"News_{now.strftime('%y_%m_%d')}.txt"
    txt_file_path = os.path.join(TXT_DIRECTORY, txt_file_name)
    
    with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
        txt_file.write(final_content + '\n\n')
    
    html_file_name = SEGMENT_TO_HTML_FILE.get(segment_content.lower(), "other.html")
    html_file_path = os.path.join(HTML_DIRECTORY, html_file_name)
    
    if not os.path.isfile(html_file_path):
        write_html_skeleton(html_file_path, segment_content)
    
    append_to_html(html_file_path, now.strftime('%Y-%m-%d %H:%M:%S'), clipboard_content)
    
    if os.path.isfile(html_file_path):
        close_html_skeleton(html_file_path)
    
    try:
        result = subprocess.run(['osascript', SCRIPT_PATH], check=True, text=True, stdout=subprocess.PIPE)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e}")
    
    move_and_record_images(url)
    time.sleep(0.3)
    os.remove(SEGMENT_FILE_PATH)
    os.remove(SITE_FILE_PATH)

if __name__ == '__main__':
    main()