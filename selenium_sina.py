import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import re

# ChromeDriver 路径
chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"  # 请替换为您的 ChromeDriver 路径

# 设置 ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

def scrape_and_save():
    driver.get("https://www.sina.com.cn/")  # 访问新浪网首页

    # 查找所有的<a>标签
    link_elements = driver.find_elements(By.TAG_NAME, "a")
    
    # 使用正则表达式来过滤中文标题
    chinese_titles = [element.text for element in link_elements if re.search(r'[\u4e00-\u9fff]+', element.text)]

    # 将数据写入 CSV 文件
    with open('/Users/yanzhang/Downloads/sina_chinese_titles.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title'])  # 写入表头
        for title in chinese_titles:
            writer.writerow([title])  # 写入每个标题

    driver.quit()

scrape_and_save()
