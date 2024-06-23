import os
import glob
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

def fetch_new_content(driver, existing_links, formatted_datetime):
    new_rows = []
    try:
        css_selector = "a[href*='/2024']"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)

        def is_valid_title(title_text):
            invalid_phrases = ['Illustration:', '/Bloomberg', 'Getty Images', '/AP Photo', '/AP', 'Photos:', 'Photo illustration', 'Source:', '/AFP', 'NurPhoto']
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
            except:
                return False
        
        for title_element in titles_elements:
            href = title_element.get_attribute('href')
            title_text = title_element.text.strip()
            if is_valid_title(title_text) and href and not any(is_similar(href, link) for link in existing_links):
                new_rows.append([formatted_datetime, title_text, href])
                existing_links.add(href)
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
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.bloomberg.com/")

    old_file_path = "/Users/yanzhang/Documents/News/site/bloomberg.html"
    old_content = get_old_content(old_file_path, 30)
    existing_links = {link for _, _, link in old_content}

    new_rows = fetch_new_content(driver, existing_links, current_datetime)
    new_rows1 = [["Bloomberg", title, link] for _, title, link in new_rows]

    driver.quit()

    if os.path.exists(old_file_path):
        os.remove(old_file_path)

    write_html(old_file_path, new_rows, old_content)
    append_to_today_html("/Users/yanzhang/Documents/News/today_eng.html", new_rows1)