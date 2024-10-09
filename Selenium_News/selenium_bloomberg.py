import os
import cv2
import time
import pyautogui
import numpy as np
from PIL import ImageGrab
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urlparse
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def is_similar(url1, url2):
    parsed_url1, parsed_url2 = urlparse(url1), urlparse(url2)
    base_url1 = f"{parsed_url1.scheme}://{parsed_url1.netloc}{parsed_url1.path}"
    base_url2 = f"{parsed_url2.scheme}://{parsed_url2.netloc}{parsed_url2.path}"
    return base_url1 == base_url2

# 截取屏幕
def capture_screen():
    # 使用PIL的ImageGrab直接截取屏幕
    screenshot = ImageGrab.grab()
    # 将截图对象转换为OpenCV格式
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return screenshot

# 查找屏幕上的图片
def find_image_on_screen(template, threshold=0.9):
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        return max_loc, template.shape
    return None, None

def get_old_content(file_path, days_ago):
    old_content = []
    if not os.path.exists(file_path):
        return old_content

    cutoff_date = datetime.now() - timedelta(days=days_ago)
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        for row in soup.find_all('tr')[1:]:  # Skip header
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            date_str, title, link = cols[0].text.strip(), cols[1].text.strip(), cols[1].find('a')['href']
            date = datetime.strptime(date_str, '%Y_%m_%d_%H')
            if date >= cutoff_date:
                old_content.append([date_str, title, link])
    return old_content

def fetch_content(driver, existing_links, formatted_datetime):
    new_rows = []
    try:
        css_selector = "a[href*='/2024']"
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
        # time.sleep(3)

        new_rows = process_titles(titles_elements, existing_links, formatted_datetime)
    except Exception as e:
        print("抓取过程中出现错误:", e)
    return new_rows

def switch_to_us_and_fetch(driver, existing_links, formatted_datetime):
    try:
        # 点击 "Asia Edition" 按钮
        region_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".media-ui-RegionPicker_region-p79mNAtF--M-"))
        )
        region_button.click()

        # 暂停以确保下拉菜单加载完毕
        time.sleep(1)

        # 点击 "US" 选项
        us_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='dropdown']//div[text()='US']"))
        )
        us_option.click()

        # 暂停以确保页面切换
        time.sleep(1)

        # 抓取US版内容
        return fetch_content(driver, existing_links, formatted_datetime)
    except Exception as e:
        print("切换到US版并抓取内容时出现错误:", e)
        return []

def process_titles(titles_elements, existing_links, formatted_datetime):
    new_rows = []
    for title_element in titles_elements:
        href = title_element.get_attribute('href')
        title_text = title_element.text.strip()

        # 删除 "Newsletter: " 字符
        if title_text.startswith("Newsletter: "):
            title_text = title_text[11:]
            
        print(f"Processing element: Href: {href}, Text: {title_text}")  # 调试信息
        if is_valid_title(title_text) and href and not any(is_similar(href, link) for link in existing_links):
            new_rows.append([formatted_datetime, title_text, href])
            existing_links.add(href)
            print(f"Added new row: {title_text}")  # 调试信息
        else:
            print(f"Skipped: {title_text}")  # 调试信息
    return new_rows

def is_valid_title(title_text):
    invalid_phrases = ['Illustration:', '/Bloomberg', 'Getty Images', '/AP Photo', '/AP', 'Photos:', 'Photo illustration', 'Source:', '/AFP', 'NurPhoto', 'SOurce:', 'WireImage']
    if any(phrase in title_text for phrase in invalid_phrases):
        return False

    if any(keyword in title_text for keyword in ['Listen', 'Watch']) and '(' in title_text and ')' in title_text:
        title_text = title_text.split(')')[1].strip()
    return True if title_text and not is_time_format(title_text) else False

def is_time_format(text):
    try:
        if len(text) in [4, 5] and ':' in text:
            parts = text.split(':')
            return all(part.isdigit() for part in parts)
        return False
        
        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()

            # 删除 "Newsletter: " 字符
            if title_text.startswith("Newsletter: "):
                title_text = title_text[11:]
                
            print(f"Processing element: Href: {href}, Text: {title_text}")  # 调试信息
            if is_valid_title(title_text) and href and not any(is_similar(href, link) for link in existing_links):
                new_rows.append([formatted_datetime, title_text, href])
                existing_links.add(href)
                print(f"Added new row: {title_text}")  # 调试信息
            else:
                print(f"Skipped: {title_text}")  # 调试信息
    except Exception as e:
        print("抓取过程中出现错误:", e)
    return new_rows

def write_html(file_path, new_rows, old_content):
    with open(file_path, 'w', encoding='utf-8') as html_file:
        html_file.write("<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n")
        for row in new_rows + old_content:
            clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>"
            html_file.write(f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n")
        html_file.write("</table></body></html>")

def append_to_today_html(today_html_path, new_rows1):
    append_content = ''.join([f"<tr><td>{row[0]}</td><td><a href='{row[2]}' target='_blank'>{row[1]}</a></td></tr>\n" for row in new_rows1])
    if os.path.exists(today_html_path):
        with open(today_html_path, 'r+', encoding='utf-8') as html_file:
            content = html_file.read()
            insertion_point = content.rindex("</table></body></html>")
            html_file.seek(insertion_point)
            html_file.write(append_content + "</table></body></html>")
    else:
        with open(today_html_path, 'w', encoding='utf-8') as html_file:
            html_file.write("<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n")
            html_file.write(append_content + "</table></body></html>")

if __name__ == "__main__":
    current_datetime = datetime.now().strftime("%Y_%m_%d_%H")
    chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"
    timeout = 5  # 设置超时时间
    template_path_accept = '/Users/yanzhang/Documents/python_code/Resource/Bloomberg_agree.png'
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.bloomberg.com/")

    template_accept = cv2.imread(template_path_accept, cv2.IMREAD_COLOR)

    if template_accept is None:
        raise FileNotFoundError(f"模板图片未能正确读取于路径 {template_path_accept}")

    found = False
    start_time = time.time()
    time.sleep(1)

    # 循环查找图片
    while not found and time.time() - start_time < timeout:
        location, shape = find_image_on_screen(template_accept)
        if location:
            print("找到图片，继续执行后续程序。")
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) // 2
            center_y = (location[1] + shape[0] // 2) // 2
                
            # 鼠标点击中心坐标
            pyautogui.click(center_x, center_y)
            found = True  # 找到图片，设置found为True以退出循环
        else:
            time.sleep(1)

    old_file_path = "/Users/yanzhang/Documents/News/site/bloomberg.html"
    old_content = get_old_content(old_file_path, 30)
    existing_links = {link for _, _, link in old_content}

    # 尝试点击 "Dismiss" 按钮
    try:
        dismiss_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'Button_text-N76nbJyFyw0-') and text()='Dismiss']"))
        )
        dismiss_button.click()
        print("Dismiss按钮已点击")
    except Exception:
        print("Dismiss按钮未出现或未点击")

    # 第一次抓取（当前页面）
    new_rows = fetch_content(driver, existing_links, current_datetime)
    
    # 更新existing_links以包含第一次抓取的结果
    existing_links.update(link for _, _, link in new_rows)
    
    # 切换到US版并再次抓取
    us_new_rows = switch_to_us_and_fetch(driver, existing_links, current_datetime)
    
    # 合并两次抓取的结果并去重
    all_new_rows = list({row[2]: row for row in new_rows + us_new_rows}.values())
    
    new_rows1 = [["Bloomberg", title, link] for _, title, link in all_new_rows]

    driver.quit()

    if os.path.exists(old_file_path):
        os.remove(old_file_path)

    write_html(old_file_path, all_new_rows, old_content)
    append_to_today_html("/Users/yanzhang/Documents/News/today_eng.html", new_rows1)
    time.sleep(1)  # 等待1秒