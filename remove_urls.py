import re

# 用于匹配以http://或https://开头，直到空格结束的字符串的正则表达式
url_pattern = re.compile(r'http[s]?://[^ ]*')

# 读取文件内容
with open('/Users/yanzhang/Downloads/a.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# 替换掉所有的URL链接
clean_content = re.sub(url_pattern, '', content)

# 将处理后的内容写回文件
with open('/Users/yanzhang/Downloads/b.txt', 'w', encoding='utf-8') as file:
    file.write(clean_content)

print('所有带有http://或https://前缀的网址链接已从文件中删除。')