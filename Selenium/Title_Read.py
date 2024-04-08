import re
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
        if self.capture:
            self.titles.append(data)

# 读取HTML文件内容
with open('/Users/yanzhang/Documents/News/today_eng.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# 创建解析器实例
parser = MyHTMLParser()

# 喂数据给解析器
parser.feed(html_content)

# 获取提取到的标题
titles = parser.titles

# 将标题拼接成一个字符串，以换行符隔开
titles_text = "\n".join(titles)

# 将提取到的标题写入文件
with open('/tmp/newstitle.txt', 'w', encoding='utf-8') as file:
    file.write(titles_text)

# 打印出提取到的文本，以便验证
print(titles_text)