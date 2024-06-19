import re
import shutil
from html.parser import HTMLParser
from math import ceil

# 创建一个子类并重写HTMLParser的方法
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.capture = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "target" and attr[1] == "_blank":
                    self.capture = True
                    self.current_data = []

    def handle_endtag(self, tag):
        if tag == "a" and self.capture:
            cleaned_data = ''.join(self.current_data).strip().strip('"').strip("'")
            self.titles.append(cleaned_data)
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.current_data.append(data.replace("\n", " ").replace("\r", " ").strip())

# 定义文件路径和备份路径
file_path = '/Users/yanzhang/Documents/News/today_eng.html'
backup_path = '/Users/yanzhang/Documents/News/site/today_eng.html'

# 读取HTML文件内容
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# 创建解析器实例
parser = MyHTMLParser()

# 喂数据给解析器
parser.feed(html_content)

# 获取提取到的标题
titles = parser.titles

# 将标题写入a.txt文件中
titles_text = "\n".join(titles)
with open('/Users/yanzhang/Documents/News/today_eng.txt', 'w', encoding='utf-8') as a_file:
    a_file.write(titles_text)

# 获取总字符数
total_chars = len(titles_text)

# 根据字符数量决定分割文件的数量
num_parts = ceil(total_chars / 3200)

# 分割标题并写入文件
start_index = 0
for i in range(num_parts):
    end_index = start_index + 3200
    if end_index >= total_chars:
        end_index = total_chars - 1
    else:
        while end_index < total_chars and titles_text[end_index] not in ['\n', '\r']:
            end_index += 1
    titles_part = titles_text[start_index:end_index].strip()  # 去掉可能多余的空白字符
    start_index = end_index + 1  # 跳过换行符

    with open(f'/tmp/segment_{i+1}.txt', 'w', encoding='utf-8') as file:
        file.write(titles_part)

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path, backup_path)

# 打印出提取到的文本，以便验证
start_index = 0
for i in range(num_parts):
    end_index = start_index + 3200
    if end_index >= total_chars:
        end_index = total_chars - 1
    else:
        while end_index < total_chars and titles_text[end_index] not in ['\n', '\r']:
            end_index += 1
    titles_part = titles_text[start_index:end_index].strip()  # 去掉可能多余的空白字符
    start_index = end_index + 1  # 跳过换行符

    # print(f"Titles Part {i+1}:")
    # print(titles_part)
    # print("\n")