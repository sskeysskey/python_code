import os
import glob
import datetime
import webbrowser
import tkinter as tk
from bs4 import BeautifulSoup
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse

def open_html_file(file_path):
    webbrowser.open('file://' + os.path.realpath(file_path), new=2)
    exit()  # 终止程序

def open_new_html_file():
    webbrowser.open('file://' + os.path.realpath(new_html_path), new=2)

#def is_similar(url1, url2):
    """
    比较两个 URL 的相似度，如果相似度超过阈值则返回 True，否则返回 False。
    主要比较 URL 的协议、主机名和路径。
    """
    #parsed_url1 = urlparse(url1)
    #parsed_url2 = urlparse(url2)

    #base_url1 = f"{parsed_url1.scheme}://{parsed_url1.netloc}{parsed_url1.path}"
    #base_url2 = f"{parsed_url2.scheme}://{parsed_url2.netloc}{parsed_url2.path}"

    #return base_url1 == base_url2

def is_similar(url1, url2):
    """
    比较两个 URL 是否相同，如果协议、主机名、路径、查询参数都相同则返回 True，否则返回 False。
    """
    parsed_url1 = urlparse(url1)
    parsed_url2 = urlparse(url2)

    # 比较协议、主机名、路径和查询参数
    return (parsed_url1.scheme == parsed_url2.scheme and
            parsed_url1.netloc == parsed_url2.netloc and
            parsed_url1.path == parsed_url2.path and
            parsed_url1.query == parsed_url2.query)

# 初始化 tkinter
root = tk.Tk()
root.withdraw()  # 不显示主窗口

# 设置窗口在屏幕正中间
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (200/2))
y_cordinate = int((screen_height/2) - (100/2)) - 100
root.geometry("{}x{}+{}+{}".format(200, 100, x_cordinate, y_cordinate))
#root.attributes('-topmost', True)  # 窗口置于最前台

# 获取当前日期
current_datetime = datetime.datetime.now()
formatted_date = current_datetime.strftime("%Y.%m.%d")  # 用于检查日期匹配

# 查找旧的 HTML 文件
file_pattern = "/Users/yanzhang/Documents/sskeysskey.github.io/news/ftchinese.html"
old_file_list = glob.glob(file_pattern)
date_found = False

if not old_file_list:
    print("未找到符合条件的旧文件。")
    # 处理未找到旧文件的情况
else:
    # 只应该有一个文件，因此可以直接获取第一个
    old_file_path = old_file_list[0]
    with open(old_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows[1:]:  # 跳过标题行
            date_cell = row.find('td')  # 获取每行的第一个单元格，即日期单元格
            if date_cell and date_cell.text.strip().startswith(formatted_date):
                date_found = True
                break

    if date_found:
        # 弹窗询问用户操作
        response = messagebox.askyesno("内容检查", f"已有当天内容 {formatted_date} 【Yes】打开文件，【No】再次爬取", parent=root)
        if response:
            # 用户选择“是”，打开当前html文件
            open_html_file(old_file_path)
            print(f"找到匹配当天日期的内容，打开文件：{old_file_path}")
            root.destroy()  # 关闭tkinter并结束程序
        else:
            # 用户选择“否”，继续执行后续代码进行重新爬取
            print("用户选择重新爬取，继续执行程序。")
    else:
        print("没有找到匹配当天日期的内容，继续执行后续代码。")

# 获取当前日期
current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
current_day = datetime.datetime.now().day
formatted_datetime = current_datetime.strftime("%Y.%m.%d_%H")

# ChromeDriver 路径
chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"

# 设置 ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

# 打开 FT 网站
driver.get("https://www.ftchinese.com/")

# 查找旧的 html 文件
file_pattern = "/Users/yanzhang/Documents/sskeysskey.github.io/news/ftchinese.html"
old_file_list = glob.glob(file_pattern)

if not old_file_list:
    print("未找到符合条件的旧文件。")
    # 处理未找到旧文件的情况
else:
    # 选择第一个找到的文件（您可能需要进一步的逻辑来选择正确的文件）
    old_file_path = old_file_list[0]

    # 读取旧文件中的所有内容
    old_content = []
    with open(old_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        rows = soup.find_all('tr')[1:]  # 跳过标题行
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:  # 确保行有足够的列
                date = cols[0].text.strip()
                title_column = cols[1]
                title = title_column.text.strip()
                # 从标题所在的列中提取链接
                link = title_column.find('a')['href'] if title_column.find('a') else None
                old_content.append([date, title, link])

    # 抓取新内容
    new_rows = []
    all_links = [old_link for _, _, old_link in old_content]  # 既有的所有链接
    premium_links = set()  # 存储已发现的premium链接数字部分

    try:
        css_selector = "a[href*='/premium/'], a[href*='interactive'], a[href*='story']"
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()

            if href and title_text:
                # 提取链接中的数字部分，假设链接结构为 https://www.ftchinese.com/premium/001101900
                link_number = href.rstrip('/').split('/')[-1]
                
                # 检查是否已存在相同数字的premium链接
                if '/premium/' in href:
                    premium_links.add(link_number)
                    
                    if not any(is_similar(href, old_link) for _, _, old_link in old_content):
                        if not any(is_similar(href, new_link) for _, _, new_link in new_rows):
                            # 如果是story链接且数字部分已存在于premium链接中，则跳过
                            if '/story/' in href and link_number in premium_links:
                                continue
                            new_rows.append([formatted_datetime, title_text, href])
                            all_links.append(href)  # 添加到所有链接的列表中

    except Exception as e:
        print("抓取过程中出现错误:", e)

    # 关闭驱动
    driver.quit()

    try:
        os.remove(old_file_path)
        print(f"文件 {old_file_path} 已被删除。")
    except OSError as e:
        print(f"错误: {e.strerror}. 文件 {old_file_path} 无法删除。")

    # 创建 HTML 文件
    new_html_path = f"/Users/yanzhang/Documents/sskeysskey.github.io/news/ftchinese.html"
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

    # 显示提示窗口
    if new_content_added:
        messagebox.showinfo("更新通知", "抓到新内容了ˆ_ˆ速看！！", parent=root)
        open_new_html_file()
        root.destroy()  # 关闭tkinter并结束程序
    else:
        messagebox.showinfo("更新通知", "Sorry，没有新东西:(", parent=root)
        root.destroy()  # 关闭tkinter并结束程序