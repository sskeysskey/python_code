from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import datetime

# 获取当前年份和月份
current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
current_day = datetime.datetime.now().day

# 动态生成文件名
file_name = f"/Users/yanzhang/Downloads/economist_{current_year}_{current_month:02d}_{current_day:02d}.csv"

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

try:
    # 使用 CSS 选择器定位所有 href 属性中包含 '2023/12' 的链接
    css_selector = f"a[href*='/{current_year}/{current_month}/']"
    # css_selector = "a[href*='2023/12']"
    titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

    # 创建或打开 CSV 文件，并准备写入
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入标题行
        writer.writerow(['Title', 'Link'])

        seen_titles = set()  # 存储已经出现过的标题

        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()  # 移除标题两端的空白字符

            # 拼接完整的 URL
            full_url = f"{href}"

            # 过滤掉包含 'podcasts' 的链接、空标题，以及重复的标题
            if 'podcasts' not in href and title_text and title_text not in seen_titles:
                seen_titles.add(title_text)
                writer.writerow([title_text, full_url])

except Exception as e:
    print("抓取过程中出现错误:", e)

# 关闭驱动
driver.quit()
