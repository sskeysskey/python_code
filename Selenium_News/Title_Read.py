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
with open('/Users/yanzhang/Documents/News/today_eng.txt', 'w', encoding='utf-8') as a_file:
    for title in titles:
        a_file.write(title + "\n")

# 获取总标题数
total_titles = len(titles)

# 根据标题数量决定分割文件的数量
if total_titles <= 50:
    num_parts = 1
elif total_titles <= 100:
    num_parts = 2
elif total_titles <= 150:
    num_parts = 3
elif total_titles <= 200:
    num_parts = 4
elif total_titles <= 250:
    num_parts = 5
elif total_titles <= 300:
    num_parts = 6
elif total_titles <= 350:
    num_parts = 7
elif total_titles <= 400:
    num_parts = 8
else:
    num_parts = 9

# 计算每个部分的大小
part_size = ceil(total_titles / num_parts)

# 分割标题并写入文件
for i in range(num_parts):
    start_index = i * part_size
    end_index = start_index + part_size
    titles_part = titles[start_index:end_index]
    titles_text = "\n".join(titles_part)
    
    with open(f'/tmp/segment_{i+1}.txt', 'w', encoding='utf-8') as file:
        file.write(titles_text)

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path, backup_path)

# 打印出提取到的文本，以便验证
for i in range(num_parts):
    start_index = i * part_size
    end_index = start_index + part_size
    titles_part = titles[start_index:end_index]
    titles_text = "\n".join(titles_part)
    
    print(f"Titles Part {i+1}:")
    print(titles_text)
    print("\n")