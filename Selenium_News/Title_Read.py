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
file_path_eng = '/Users/yanzhang/Documents/News/today_eng.html'
backup_path_eng = '/Users/yanzhang/Documents/News/site/today_eng.html'
file_path_jpn = '/Users/yanzhang/Documents/News/today_jpn.html'
backup_path_jpn = '/Users/yanzhang/Documents/News/site/today_jpn.html'

# 读取HTML文件内容
with open(file_path_eng, 'r', encoding='utf-8') as file:
    html_content_eng = file.read()

# 创建解析器实例
parser_eng = MyHTMLParser()

# 喂数据给解析器
parser_eng.feed(html_content_eng)

# 获取提取到的标题
titles_eng = parser_eng.titles

# 将标题写入a.txt文件中
titles_text_eng = "\n".join(titles_eng)
with open('/Users/yanzhang/Documents/News/today_eng.txt', 'w', encoding='utf-8') as a_file:
    a_file.write(titles_text_eng)

# 获取总字符数
total_chars_eng = len(titles_text_eng)

# 根据字符数量决定分割文件的数量
num_parts_eng = ceil(total_chars_eng / 3000)

# 分割标题并写入文件
start_index = 0
for i in range(num_parts_eng):
    end_index = start_index + 3000
    if end_index >= total_chars_eng:
        end_index = total_chars_eng  # 修改为 total_chars_eng
    else:
        while end_index < total_chars_eng and titles_text_eng[end_index] not in ['\n', '\r']:
            end_index += 1
    titles_part = titles_text_eng[start_index:end_index].strip()  # 去掉可能多余的空白字符
    start_index = end_index + 1  # 跳过换行符

    with open(f'/tmp/segment_{i+1}.txt', 'w', encoding='utf-8') as file:
        file.write(titles_part)

    # 防止 start_index 超过 total_chars_eng 导致最后一个文件为空
    if start_index >= total_chars_eng:
        break

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path_eng, backup_path_eng)

# 处理日文文件
# 读取HTML文件内容
with open(file_path_jpn, 'r', encoding='utf-8') as file:
    html_content_jpn = file.read()

# 创建解析器实例
parser_jpn = MyHTMLParser()

# 喂数据给解析器
parser_jpn.feed(html_content_jpn)

# 获取提取到的标题
titles_jpn = parser_jpn.titles

# 将标题写入a.txt文件中
titles_text_jpn = "\n".join(titles_jpn)
with open('/Users/yanzhang/Documents/News/today_jpn.txt', 'w', encoding='utf-8') as a_file:
    a_file.write(titles_text_jpn)

# 获取总字符数
total_chars_jpn = len(titles_text_jpn)

# 平均分割成两部分
mid_index = total_chars_jpn // 2

# 找到适合的分割点
while mid_index < total_chars_jpn and titles_text_jpn[mid_index] not in ['\n', '\r']:
    mid_index += 1

# 分割标题并写入文件
titles_part_1 = titles_text_jpn[0:mid_index].strip()
titles_part_2 = titles_text_jpn[mid_index:].strip()

# 写入文件
with open(f'/tmp/segment_{num_parts_eng + 1}.txt', 'w', encoding='utf-8') as file:
    file.write(titles_part_1)

with open(f'/tmp/segment_{num_parts_eng + 2}.txt', 'w', encoding='utf-8') as file:
    file.write(titles_part_2)

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path_jpn, backup_path_jpn)