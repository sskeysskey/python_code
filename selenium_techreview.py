import os
import glob
import csv
import datetime
import tkinter as tk
from bs4 import BeautifulSoup
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC

# 初始化 tkinter
root = tk.Tk()
root.withdraw()  # 不显示主窗口

# 设置窗口在屏幕正中间
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (200/2))
y_cordinate = int((screen_height/2) - (100/2)) - 100
root.geometry("{}x{}+{}+{}".format(200, 100, x_cordinate, y_cordinate))

root.attributes('-topmost', True)  # 窗口置于最前台

# 获取当前日期
current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
current_day = datetime.datetime.now().day
current_datetime = datetime.datetime.now()
formatted_datetime = current_datetime.strftime("%Y.%m.%d_%H")

# ChromeDriver 路径
chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"

# 设置 ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

# 打开 Economist 网站
driver.get("https://www.technologyreview.com/")

#try:
    # 使用 WebDriverWait 等待 'Accept all cookies' 按钮变为可点击状态
    #WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
    #print("已点击 'Accept all cookies' 按钮")
#except Exception as e:
    #print(f"点击 'Accept all cookies' 按钮时出错: {e}")

# 查找旧的 CSV 文件
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
        table = soup.find('table')  # 假设数据存储在第一个表格中
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                old_content.append(cols)

    # 抓取新内容
    new_rows = []
    try:
        css_selector = f"a[href*='technologyreview.com/{current_year}/{current_month}/']"
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()

            # 检查新内容是否重复，并且不在旧文件中
            if title_text and 'podcasts' not in href and not any(title_text in row or href in row for row in new_rows + old_content):
                new_rows.append([formatted_datetime, title_text, href])

    except Exception as e:
        print("抓取过程中出现错误:", e)

    # 关闭驱动
    driver.quit()

    # 创建 HTML 文件
    new_html_path = f"/Users/yanzhang/Documents/techreview_{current_year}_{current_month:02d}_{current_day:02d}.html"
    with open(new_html_path, 'w', encoding='utf-8') as html_file:
        # 写入 HTML 基础结构和表格开始标签
        html_file.write("<html><body><table border='1'>\n")

        # 写入标题行，如果旧文件有标题行
        if old_content:
            html_file.write("<tr><th>" + "</th><th>".join(old_content[0]) + "</th></tr>\n")
            old_content = old_content[1:]

        # 写入新抓取的内容
        for row in new_rows:
            # 将链接转换为可点击的 HTML 链接
            clickable_link = f"<a href='{row[2]}' target='_blank'>{row[2]}</a>"
            # 替换原始链接为可点击链接
            row[2] = clickable_link
            html_file.write("<tr><td>" + "</td><td>".join(row) + "</td></tr>\n")

        # 写入旧内容
        for row in old_content:
            # 检查是否存在链接，并转换为可点击的 HTML 链接
            if len(row) > 2 and row[2].startswith("http"):
                clickable_link = f"<a href='{row[2]}' target='_blank'>{row[2]}</a>"
                row[2] = clickable_link
            html_file.write("<tr><td>" + "</td><td>".join(row) + "</td></tr>\n")

        # 结束表格和 HTML 结构
        html_file.write("</table></body></html>")

    # 重命名旧文件
    new_file_name = f"/Users/yanzhang/Documents/techreview_{current_year}_{current_month:02d}_{current_day:02d}.html"
    os.rename(old_file_path, new_file_name)

    # 显示提示窗口
    #if new_content_added:
        #messagebox.showinfo("更新通知", "有新内容哦ˆ_ˆ速看！！", parent=root)
    #else:
        #messagebox.showinfo("更新通知", "Sorry，没有新东西:(", parent=root)