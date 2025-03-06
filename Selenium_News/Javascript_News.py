import os
import time
import subprocess
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import glob

def is_similar(url1, url2):
    """
    比较两个URL是否只在参数不同或其他细微处不同，
    通过比较URL的scheme、netloc和path判定是否相似。
    """
    parsed_url1, parsed_url2 = urlparse(url1), urlparse(url2)
    base_url1 = f"{parsed_url1.scheme}://{parsed_url1.netloc}{parsed_url1.path}"
    base_url2 = f"{parsed_url2.scheme}://{parsed_url2.netloc}{parsed_url2.path}"
    return base_url1 == base_url2

def get_old_content(file_path, days_ago):
    """
    读取旧的HTML文件，获取指定天数内的数据（基于<tr><td>结构）。
    """
    old_content = []
    if not os.path.exists(file_path):
        return old_content

    cutoff_date = datetime.now() - timedelta(days=days_ago)
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        for row in soup.find_all('tr')[1:]:  # 跳过表头
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            date_str, title = cols[0].text.strip(), cols[1].text.strip()
            link = cols[1].find('a')['href'] if cols[1].find('a') else ''
            date = datetime.strptime(date_str, '%Y_%m_%d_%H')
            if date >= cutoff_date:
                old_content.append([date_str, title, link])
    return old_content

def get_new_content_from_files():
    """
    读取Downloads目录下以bloomberg_开头的HTML文件内容
    """
    new_content = []
    download_dir = "/Users/yanzhang/Downloads/"
    bloomberg_files = glob.glob(os.path.join(download_dir, "bloomberg_*.html"))
    
    current_datetime = datetime.now().strftime("%Y_%m_%d_%H")
    
    for file_path in bloomberg_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            for row in soup.find_all('tr')[1:]:  # 跳过表头
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                date_str = cols[0].text.strip() if len(cols) > 0 else current_datetime
                title = cols[1].text.strip() if len(cols) > 1 else ""
                link = cols[1].find('a')['href'] if cols[1].find('a') else ''
                if title and link:
                    new_content.append([date_str, title, link])
    
    return new_content

def write_html(file_path, new_rows, old_content):
    """
    将新的抓取结果与旧内容写入同一个HTML文件，包含表格结构，
    并进行完整性校验。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as html_file:
            html_file.write("<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n")
            for row in new_rows + old_content:
                clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>"
                html_file.write(f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n")
            html_file.write("</table></body></html>")
            html_file.flush()
            os.fsync(html_file.fileno())

        # 验证完整性
        with open(file_path, 'r', encoding='utf-8') as verify_file:
            content = verify_file.read()
            if not content.endswith("</table></body></html>"):
                raise IOError("File writing verification failed")
    except Exception as e:
        print(f"Error writing to file: {e}")
        raise

def append_to_today_html(today_html_path, new_rows1):
    """
    将新增的抓取结果追加到today_eng.html文件末尾，并进行文件完整性校验。
    """
    append_content = ''.join([
        f"<tr><td>{row[0]}</td><td><a href='{row[2]}' target='_blank'>{row[1]}</a></td></tr>\n"
        for row in new_rows1
    ])
    try:
        if os.path.exists(today_html_path):
            with open(today_html_path, 'r+', encoding='utf-8') as html_file:
                content = html_file.read()
                insertion_point = content.rindex("</table></body></html>")
                html_file.seek(insertion_point)
                html_file.write(append_content + "</table></body></html>")
                html_file.flush()
                os.fsync(html_file.fileno())
        else:
            with open(today_html_path, 'w', encoding='utf-8') as html_file:
                html_file.write("<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n")
                html_file.write(append_content + "</table></body></html>")
                html_file.flush()
                os.fsync(html_file.fileno())

        with open(today_html_path, 'r', encoding='utf-8') as verify_file:
            content = verify_file.read()
            if not content.endswith("</table></body></html>"):
                raise IOError("File writing verification failed")
    except Exception as e:
        print(f"Error writing to file: {e}")
        raise

def count_bloomberg_files():
    """
    计算Downloads目录中bloomberg_开头的文件数量
    """
    download_dir = "/Users/yanzhang/Downloads/"
    bloomberg_files = glob.glob(os.path.join(download_dir, "bloomberg_*.html"))
    return len(bloomberg_files)

def open_webpage_and_monitor():
    """
    打开Bloomberg页面并监控下载文件
    """
    download_dir = "/Users/yanzhang/Downloads/"
    
    # 清理可能已存在的bloomberg_*.html文件
    existing_files = glob.glob(os.path.join(download_dir, "bloomberg_*.html"))
    for file in existing_files:
        try:
            os.remove(file)
            print(f"Removed existing file: {file}")
        except Exception as e:
            print(f"Error removing file {file}: {e}")
    
    # 打开第一个页面
    print("Opening Bloomberg main page...")
    webbrowser.open("https://bloomberg.com/")
    
    # 等待第一个文件下载
    print("Waiting for first file download...")
    while count_bloomberg_files() < 1:
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\nFirst file detected!")
    
    # 打开第二个页面
    print("Opening Bloomberg Asia page...")
    webbrowser.open("https://www.bloomberg.com/asia")
    
    # 等待第二个文件下载
    print("Waiting for second file download...")
    while count_bloomberg_files() < 2:
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\nSecond file detected!")
    print("All required files downloaded. Processing...")
    
    # AppleScript 代码 (按下 Command+W 快捷键)
    applescript = '''
    tell application "System Events"
    	repeat 2 times
            key code 13 using command down
            delay 0.5
        end repeat
    end tell
    '''

    # 使用 subprocess 执行 AppleScript
    subprocess.run(['osascript', '-e', applescript])

    applescript_code = 'display dialog "文件已下载！" buttons {"OK"} default button "OK"'
    subprocess.run(['osascript', '-e', applescript_code], check=True)
    print("Please close the Bloomberg pages manually.")
    
    # 等待一会儿，以便用户关闭页面
    time.sleep(5)

if __name__ == "__main__":
    # 新增: 打开网页并监控下载文件
    open_webpage_and_monitor()
    
    current_datetime = datetime.now().strftime("%Y_%m_%d_%H")

    # 读取旧文件内容
    old_file_path = "/Users/yanzhang/Documents/News/backup/site/bloomberg.html"
    old_content = get_old_content(old_file_path, 30)
    
    # 获取旧文件中的链接列表(用于去重)
    existing_links = {link for _, _, link in old_content}
    
    # 从两个新文件中读取内容
    new_content = get_new_content_from_files()
    
    # 根据is_similar规则排重
    new_rows = []
    for date_str, title, link in new_content:
        is_duplicate = False
        for existing_link in existing_links:
            if is_similar(link, existing_link):
                is_duplicate = True
                break
        if not is_duplicate:
            new_rows.append([date_str, title, link])
            existing_links.add(link)  # 将新链接添加到已存在列表中，防止新内容中有重复

    # 转换为today_eng.html需要的格式
    new_rows1 = [["Bloomberg", title, link] for date_str, title, link in new_rows]

    # 写入bloomberg.html并追加到today_eng.html
    if new_rows:
        write_html(old_file_path, new_rows, old_content)
        append_to_today_html("/Users/yanzhang/Documents/News/today_eng.html", new_rows1)
        print(f"Added {len(new_rows)} new articles to files")
    else:
        print("No new content to add")