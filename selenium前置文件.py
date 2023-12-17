import os
import glob
import csv
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 获取当前日期
current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
current_day = datetime.datetime.now().day
formatted_date = f"{current_year}.{current_month:02d}.{current_day:02d}"

# ChromeDriver 路径
chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"

# 设置 ChromeDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service)

# 打开 Economist 网站
driver.get("https://www.economist.com/")

# 智能等待弹窗出现
try:
    # 等待 iframe 加载完成
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_921614")))
    
    # 在 iframe 中等待“Accept all”按钮可点击并点击它
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Accept all']"))).click()
    print("已点击 iframe 中的接受 cookie 按钮")
    
    # 切换回主文档
    driver.switch_to.default_content()

except Exception as e:
    print("尝试点击 iframe 中的 cookie 同意按钮时出现错误:", e)
    driver.switch_to.default_content()

# 查找旧的 CSV 文件
file_pattern = "/Users/yanzhang/Downloads/economist_*.csv"
old_file_list = glob.glob(file_pattern)
if not old_file_list:
    print("未找到符合条件的旧文件。")
    # 处理未找到旧文件的情况
else:
    # 选择第一个找到的文件（您可能需要进一步的逻辑来选择正确的文件）
    old_file_path = old_file_list[0]

    # 读取旧文件中的所有内容
    old_content = []
    with open(old_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        old_content = list(reader)

    # 抓取新内容
    new_rows = []
    try:
        css_selector = f"a[href*='/{current_year}/{current_month}/']"
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()

            # 检查新内容是否重复，并且不在旧文件中
            if title_text and 'podcasts' not in href and not any(title_text in row for row in new_rows + old_content):
                new_rows.append([formatted_date, title_text, href])

    except Exception as e:
        print("抓取过程中出现错误:", e)

    # 关闭驱动
    driver.quit()

    # 将新内容加到旧内容的前面，并写回文件
    with open(old_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 先写标题行，如果旧文件有标题行
        if old_content:
            writer.writerow(old_content[0])
            old_content = old_content[1:]

        # 写入新抓取的内容
        writer.writerows(new_rows)

        # 写入旧内容
        writer.writerows(old_content)

    # 重命名旧文件
    new_file_name = f"/Users/yanzhang/Downloads/economist_{current_year}_{current_month:02d}_{current_day:02d}.csv"
    os.rename(old_file_path, new_file_name)
