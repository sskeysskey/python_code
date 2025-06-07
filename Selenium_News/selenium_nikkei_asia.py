import os
import glob
import time
import pyautogui
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urlparse
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def is_similar(url1, url2):
    """
    比较两个 URL 的相似度，如果相似度超过阈值则返回 True，否则返回 False。
    主要比较 URL 的协议、主机名和路径。
    """
    parsed_url1 = urlparse(url1)
    parsed_url2 = urlparse(url2)

    base_url1 = f"{parsed_url1.scheme}://{parsed_url1.netloc}{parsed_url1.path}"
    base_url2 = f"{parsed_url2.scheme}://{parsed_url2.netloc}{parsed_url2.path}"

    return base_url1 == base_url2

# 获取当前日期
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y_%m_%d_%H")

# ChromeDriver 路径
chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"

# 设置 ChromeDriver
chrome_options = Options()
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.115" # 你可以更新为一个最新的Chrome User-Agent
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# --- 性能相关设置 ---
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片加载

# 打开 nikkei asia 网站
driver.get("https://asia.nikkei.com/")

# 查找旧的 html 文件
file_pattern = "/Users/yanzhang/Documents/News/backup/site/nikkei_asia.html"
old_file_list = glob.glob(file_pattern)

old_content = []
if old_file_list:
    old_file_path = old_file_list[0]
    seven_days_ago = current_datetime - timedelta(days=10)

    try:
        with open(old_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            rows = soup.find_all('tr')[1:]  # 跳过标题行
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:  # 确保行有足够的列
                    date_str = cols[0].text.strip()
                    # 解析日期字符串
                    date = datetime.strptime(date_str, '%Y_%m_%d_%H')
                    # 若日期大于等于50天前的日期，则保留
                    if date >= seven_days_ago:
                        title_column = cols[1]
                        title = title_column.text.strip()
                        # 从标题所在的列中提取链接
                        link = title_column.find('a')['href'] if title_column.find('a') else None
                        old_content.append([date_str, title, link])
    except OSError as e:
        print(f"读取文件时出错: {e}")

# 抓取新内容
new_rows = []
new_rows1 = []
all_links = [old_link for _, _, old_link in old_content]  # 既有的所有链接

for _ in range(4):
    pyautogui.scroll(-80)
    time.sleep(0.2)

# 1. 需要特殊处理的版块
SECTIONS = ["Spotlight", "Business"]

css_selector = ", ".join(
    f"a[href*='/{section}/']:not(.label-link)" for section in SECTIONS
)

try:
    titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

    for title_element in titles_elements:
        href = title_element.get_attribute('href')
        title_text = title_element.text.strip()

        if not (href and title_text):
            continue

        # 一般性的排除关键字
        general_keywords_to_exclude = [
            'Podcast', 'sports', '/music/', 'weather', '/books/', 'food',
            'The-Future-of-Asia', 'Your-Week-in-Asia'
        ]
        if any(keyword in href for keyword in general_keywords_to_exclude):
            continue

        # Spotlight/Business 结构判断
        skip_due_to_structure = False
        try:
            parsed_url = urlparse(href)
            # 仅对 asia.nikkei.com 生效
            if parsed_url.netloc == "asia.nikkei.com":
                # 提取所有非空的 path segment
                path_segments = [
                    seg for seg in parsed_url.path.strip("/").split("/") if seg
                ]
                # 如果第一个 segment 在 SECTIONS 里，并且恰好只有两个 segment
                # （即 /Spotlight/分类 or /Business/分类），就跳过
                if (
                    path_segments
                    and path_segments[0] in SECTIONS
                    and len(path_segments) == 2
                ):
                    skip_due_to_structure = True

        except ValueError:
            # URL 格式异常也跳过
            skip_due_to_structure = True

        if skip_due_to_structure:
            continue

        # 滤重逻辑：和 old_content、new_rows 里已有的链接比较相似度
        if not any(is_similar(href, old_link) for _, _, old_link in old_content):
            if not any(is_similar(href, new_link) for _, _, new_link in new_rows):
                new_rows.append([formatted_datetime, title_text, href])
                new_rows1.append(["NikkeiAsia", title_text, href])
                all_links.append(href)

except Exception as e:
    print("抓取过程中出现错误:", e)

# 关闭驱动
driver.quit()

if old_file_list:
    try:
        os.remove(old_file_path)
        print(f"文件 {old_file_path} 已被删除。")
    except OSError as e:
        print(f"错误: {e.strerror}. 文件 {old_file_path} 无法删除。")

# 创建 HTML 文件
new_html_path = f"/Users/yanzhang/Documents/News/backup/site/nikkei_asia.html"
with open(new_html_path, 'w', encoding='utf-8') as html_file:
    # 写入 HTML 基础结构和表格开始标签
    html_file.write("<html><body><table border='1'>\n")

    # 写入标题行
    html_file.write("<tr><th>Date</th><th>Title</th></tr>\n")

    # 写入新抓取的内容
    new_content_added = False
    for row in new_rows:
        clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>"
        html_file.write(f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n")
        new_content_added = True

    # 写入旧内容
    for row in old_content:
        clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>" if row[2] else row[1]
        html_file.write(f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n")

    # 结束表格和 HTML 结构
    html_file.write("</table></body></html>")

if new_rows1:
    # 创建用于翻译的每日新闻总表html
    today_html_path = "/Users/yanzhang/Documents/News/today_eng.html"
    file_exists = os.path.isfile(today_html_path)

    # 准备要追加的内容
    append_content = ""
    for row in new_rows1:
        clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>"
        append_content += f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n"

    # 如果文件已存在，先删除末尾的HTML结束标签，再追加新内容，最后重新添加结束标签
    closing_tag = "</table></body></html>"
    if file_exists:
        # 读取整个文件内容，并去掉原有的结束标签
        with open(today_html_path, 'r', encoding='utf-8') as html_file:
            content = html_file.read()
        
        # 如果存在结束标签，则将其移除
        if closing_tag in content:
            content = content.replace(closing_tag, "")
        
        # 拼接新内容和完整的结束标签
        new_content = content + append_content + closing_tag

        # 以写入模式完整覆盖原文件，确保不会残留任何多余数据
        with open(today_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(new_content)
    else:
        # 如果文件是新建的，添加新内容和HTML结束标签
        with open(today_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write("<html><body><table border='1'>\n")
            html_file.write("<tr><th>site</th><th>Title</th></tr>\n")
            html_file.write(append_content)
            html_file.write(closing_tag)
            html_file.flush()
            os.fsync(html_file.fileno())
