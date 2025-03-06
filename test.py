def fetch_content(driver, existing_links, formatted_datetime):
    """
    抓取当前页面满足CSS选择器的所有链接，同时移除已有链接，返回新增数据。
    """
    new_rows = []
    try:
        css_selector = "a[href*='/2025']"
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        titles_elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
        new_rows = process_titles(titles_elements, existing_links, formatted_datetime)
    except Exception as e:
        print("抓取过程中出现错误:", e)
    return new_rows

def process_titles(titles_elements, formatted_datetime):
    new_rows = []
    for title_element in titles_elements:
        href = title_element.get_attribute('href')
        title_text = title_element.text.strip()

        if title_text.startswith("Newsletter: "):
            title_text = title_text[11:]

        # 跳过包含 '/videos/2025' 的链接
        if '/videos/2025' in href:
            print(f"Skipped video link: {href}")
            continue

        print(f"Processing element: Href: {href}, Text: {title_text}")
        if is_valid_title(title_text) and href:
            new_rows.append([formatted_datetime, title_text, href])
            print(f"Added new row: {title_text}")
        else:
            print(f"Skipped: {title_text}")
    return new_rows

def is_valid_title(title_text):
    """
    判断标题是否有效，过滤包含特定短语的标题，以及纯时间格式的标题。
    """
    invalid_phrases = [
        'Illustration:', '/Bloomberg', 'Getty Images', '/AP Photo', '/AP', 'Photos:',
        'Photo illustration', 'Source:', '/AFP', 'NurPhoto', 'SOurce:', 'WireImage',
        'Listen (', 'Podcast:'
    ]
    if any(phrase in title_text for phrase in invalid_phrases):
        return False

    if any(keyword in title_text for keyword in ['Listen', 'Watch']) and '(' in title_text and ')' in title_text:
        title_text = title_text.split(')')[1].strip()
    return True if title_text and not is_time_format(title_text) else False

def is_time_format(text):
    """
    判断文本是否是类似'4:57'这样纯时间格式。
    """
    try:
        if len(text) in [4, 5] and ':' in text:
            parts = text.split(':')
            return all(part.isdigit() for part in parts)
        return False
    except:
        return False


def write_html(file_path, new_rows):
    """
    将新的抓取结果与旧内容写入同一个HTML文件，包含表格结构，
    并进行完整性校验。
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as html_file:
            html_file.write("<html><body><table border='1'>\n<tr><th>Date</th><th>Title</th></tr>\n")
            for row in new_rows:
                clickable_title = f"<a href='{row[2]}' target='_blank'>{row[1]}</a>"
                html_file.write(f"<tr><td>{row[0]}</td><td>{clickable_title}</td></tr>\n")
            html_file.write("</table></body></html>")
            html_file.flush()
            os.fsync(html_file.fileno())

        # 验证完整性
        with open(file_path, 'r', encoding='utf-8') as verify_file:
            content = verify_file.read()
            if not content.endswith("</table></body></html>"):
                raise IOError("File writing verification failed")
    except Exception as e:
        print(f"Error writing to file: {e}")
        raise

if __name__ == "__main__":
    current_datetime = datetime.now().strftime("%Y_%m_%d_%H")
    chrome_driver_path = "/Users/yanzhang/Downloads/backup/chromedriver"
    old_file_path = "/Users/yanzhang/Documents/News/backup/site/bloomberg.html"
    
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.bloomberg.com/")

    # 第一次抓取（当前页面）
    new_rows = fetch_content(driver, current_datetime)
    
    new_rows1 = [["Bloomberg", title, link] for _, title, link in new_rows]

    driver.quit()

    # 写入bloomberg.html并追加到today_eng.html
    write_html(old_file_path, new_rows)
    append_to_today_html("/Users/yanzhang/Documents/News/today_eng.html", new_rows1)