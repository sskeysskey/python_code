import os
import html
import pyperclip
import subprocess
from time import sleep
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
}

def get_clipboard_content():
    content = pyperclip.paste()
    if content:
        return '\n'.join(line.strip() for line in content.splitlines() if line.strip())
    return ""

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
    clipboard_content = get_clipboard_content()
    segment_content = read_file(SEGMENT_FILE_PATH)
    site_content = read_file(SITE_FILE_PATH)
    site_content_with_tags = f'<document>{site_content}</document>请用中文详细总结这篇文章'
    
    final_content = f"{segment_content}\n{site_content_with_tags}\n\n{clipboard_content}"
    
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
    
    sleep(1)
    os.remove(SEGMENT_FILE_PATH)
    os.remove(SITE_FILE_PATH)

if __name__ == '__main__':
    main()