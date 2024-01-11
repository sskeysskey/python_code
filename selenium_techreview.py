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

def open_html_file(file_path):
    webbrowser.open('file://' + os.path.realpath(file_path), new=2)
    exit()  # 终止程序

def open_new_html_file():
    webbrowser.open('file://' + os.path.realpath(new_html_path), new=2)

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
file_pattern = "/Users/yanzhang/Documents/techreview_*.html"
old_file_list = glob.glob(file_pattern)
date_found = False

if not old_file_list:
    print("未找到符合条件的旧文件。")
    # 处理未找到旧文件的情况
else:
    for old_file_path in old_file_list:
        with open(old_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                for col in cols:
                    # 我们只检查日期部分，忽略小时部分
                    if col.text.strip().startswith(formatted_date):
                        date_found = True
                        break
                if date_found:
                    break
        if date_found:
            # 弹窗询问用户操作
            response = messagebox.askyesno("内容检查", "已有当天内容 【Yes】打开文件，【NO】重新爬取。你的选择是？", parent=root)
            if response:
            # 用户选择“是”，打开当前html文件
                open_html_file(old_file_path)
                print(f"找到匹配当天日期的内容，打开文件：{old_file_path}")
                root.destroy()  # 关闭tkinter并结束程序
                break
            else:
                # 用户选择“否”，继续执行后续代码进行重新爬取
                print("用户选择重新爬取，继续执行程序。")
                
if not date_found:
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

# 打开 Economist 网站
driver.get("https://www.technologyreview.com/")

# 查找旧的 html 文件
file_pattern = "/Users/yanzhang/Documents/techreview_*.html"
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
            if len(cols) >= 3:  # 确保行有足够的列
                date = cols[0].text
                title = cols[1].text
                link = cols[2].find('a')['href'] if cols[2].find('a') else None
                old_content.append([date, title, link])

    # 抓取新内容
    new_rows = []
    all_links = [old_link for _, _, old_link in old_content]  # 既有的所有链接
    
    try:
        css_selector = f"a[href*='technologyreview.com/{current_year}/']"
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()

            if href and title_text:
                #print(f"标题: {title_text}, 链接: {href}")

                if 'podcasts' not in href:
                    if not any(href == old_link for _, _, old_link in old_content):
                        if not any(href == new_link for _, _, new_link in new_rows):
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
    new_html_path = f"/Users/yanzhang/Documents/techreview_{current_year}_{current_month:02d}_{current_day:02d}.html"
    with open(new_html_path, 'w', encoding='utf-8') as html_file:
        # 写入 HTML 基础结构和表格开始标签
        html_file.write("<html><body><table border='1'>\n")

        # 写入标题行
        html_file.write("<tr><th>Date</th><th>Title</th><th>Link</th></tr>\n")

        # 写入新抓取的内容
        new_content_added = False
        for row in new_rows:
            clickable_link = f"<a href='{row[2]}' target='_blank'>链接</a>"
            html_file.write(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{clickable_link}</td></tr>\n")
            new_content_added = True
        
        # 写入旧内容
        for row in old_content:
            link_html = f"<a href='{row[2]}' target='_blank'>链接</a>" if row[2] else "链接"
            html_file.write(f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{link_html}</td></tr>\n")

        # 结束表格和 HTML 结构
        html_file.write("</table></body></html>")

    # 显示提示窗口
    if new_content_added:
        messagebox.showinfo("更新通知", "有新内容哦ˆ_ˆ速看！！", parent=root)
        open_new_html_file()
        root.destroy()  # 关闭tkinter并结束程序
    else:
        messagebox.showinfo("更新通知", "Sorry，没有新东西:(", parent=root)
        root.destroy()  # 关闭tkinter并结束程序