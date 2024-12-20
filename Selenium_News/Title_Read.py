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

def add_line_numbers(text):
    """为文本添加行号"""
    lines = text.split('\n')
    return '\n'.join(f"{i+1}、{line}" for i, line in enumerate(lines) if line.strip())

# 文件路径定义
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

# 添加行号并写入主文件
titles_text_eng = add_line_numbers("\n".join(titles_eng))
with open('/Users/yanzhang/Documents/News/today_eng.txt', 'w', encoding='utf-8') as a_file:
    a_file.write(titles_text_eng)

# 计算分割
total_chars_eng = len(titles_text_eng)
num_parts_eng = ceil(total_chars_eng / 3000)

# 分割并写入子文件
titles_lines = titles_text_eng.split('\n')
lines_per_file = ceil(len(titles_lines) / num_parts_eng)
current_line = 0

for i in range(num_parts_eng):
    start_line = i * lines_per_file
    end_line = min((i + 1) * lines_per_file, len(titles_lines))
    
    # 获取当前部分的行，并重新编号
    current_lines = titles_lines[start_line:end_line]
    # 移除旧的行号并添加新的行号
    current_lines = [line.split('、', 1)[1] if '、' in line else line for line in current_lines]
    numbered_lines = [f"{j+1}、{line}" for j, line in enumerate(current_lines) if line.strip()]
    
    with open(f'/tmp/segment_{i+1}.txt', 'w', encoding='utf-8') as file:
        file.write('\n'.join(numbered_lines))

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path_eng, backup_path_eng)

try:
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

    # 添加行号并写入主文件
    titles_text_jpn = add_line_numbers("\n".join(titles_jpn))
    with open('/Users/yanzhang/Documents/News/today_jpn.txt', 'w', encoding='utf-8') as a_file:
        a_file.write(titles_text_jpn)

    # 分割日文文件为两部分
    titles_lines_jpn = titles_text_jpn.split('\n')
    mid_point = len(titles_lines_jpn) // 2

    # 处理第一部分
    first_part = titles_lines_jpn[:mid_point]
    first_part = [line.split('、', 1)[1] if '、' in line else line for line in first_part]
    first_part_numbered = [f"{i+1}、{line}" for i, line in enumerate(first_part) if line.strip()]

    # 处理第二部分
    second_part = titles_lines_jpn[mid_point:]
    second_part = [line.split('、', 1)[1] if '、' in line else line for line in second_part]
    second_part_numbered = [f"{i+1}、{line}" for i, line in enumerate(second_part) if line.strip()]

    # 写入分割后的文件
    with open(f'/tmp/segment_{num_parts_eng + 1}.txt', 'w', encoding='utf-8') as file:
        file.write('\n'.join(first_part_numbered))

    with open(f'/tmp/segment_{num_parts_eng + 2}.txt', 'w', encoding='utf-8') as file:
        file.write('\n'.join(second_part_numbered))

    # 备份日文HTML文件
    shutil.copyfile(file_path_jpn, backup_path_jpn)

except FileNotFoundError:
    print(f"Warning: {file_path_jpn} 文件不存在，已跳过日文文件的处理。")