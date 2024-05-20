import re
import shutil
from html.parser import HTMLParser

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

    def handle_endtag(self, tag):
        if tag == "a":
            self.capture = False

    def handle_data(self, data):
        if self.capture and data.strip():  # 添加检查条件以确保data不只包含空白字符
            self.titles.append(data.strip())

# 定义文件路径和备份路径
file_path = '/Users/yanzhang/Documents/News/today_eng.html'
backup_path = '/Users/yanzhang/Documents/News/backup/today_eng.html'

# 读取HTML文件内容
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# 创建解析器实例
parser = MyHTMLParser()

# 喂数据给解析器
parser.feed(html_content)

# 获取提取到的标题
titles = parser.titles

# 将标题列表分成两部分
middle_index = len(titles) // 2
titles_part1 = titles[:middle_index]
titles_part2 = titles[middle_index:]

# 将两部分标题拼接成字符串，以换行符隔开
titles_text1 = "\n".join(titles_part1)
titles_text2 = "\n".join(titles_part2)

# 将两部分标题写入到不同的文件中
with open('/tmp/segment_1.txt', 'w', encoding='utf-8') as file1:
    file1.write(titles_text1)
with open('/tmp/segment_2.txt', 'w', encoding='utf-8') as file2:
    file2.write(titles_text2)

# 备份HTML源文件到指定目录，如果文件已存在则覆盖
shutil.copyfile(file_path, backup_path)

# 打印出提取到的文本，以便验证
print("Titles Part 1:")
print(titles_text1)
print("\nTitles Part 2:")
print(titles_text2)