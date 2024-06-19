import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 设置保存路径
save_path = "/Users/yanzhang/Downloads"

# 初始化浏览器选项
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")

# 安装并启动浏览器
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 获取初始页面内容
url = "https://lexica.art/"
driver.get(url)
time.sleep(3)  # 等待页面加载

# 解析页面内容
soup = BeautifulSoup(driver.page_source, "html.parser")
links = soup.find_all("a", href=True)

# 获取前10个符合条件的链接
image_links = []
for link in links:
    if link["href"].startswith("/prompt/"):
        image_links.append(link["href"])
        if len(image_links) >= 10:
            break

# 遍历每个链接，点击并获取图片地址
for relative_link in image_links:
    full_link = f"https://lexica.art{relative_link}"
    driver.get(full_link)
    time.sleep(3)  # 等待页面加载
    img_soup = BeautifulSoup(driver.page_source, "html.parser")
    img_tag = img_soup.find("img", {"class": "relative z-20"})
    if img_tag and "src" in img_tag.attrs:
        img_url = img_tag["src"]
        img_name = img_url.split("/")[-1]
        img_path = os.path.join(save_path, img_name)
        
        # 下载图片
        img_data = requests.get(img_url).content
        with open(img_path, 'wb') as handler:
            handler.write(img_data)
        print(f"Downloaded {img_name} to {save_path}")

# 关闭浏览器
driver.quit()