import os
import glob
from bs4 import BeautifulSoup

# 定义文件路径
wsj_file = '/Users/yanzhang/Documents/News/today_wsjcn.html'

# 读取两个文件的内容
with open(wsj_file, 'r', encoding='utf-8') as f:
    wsj_html = f.read()

with open(today_cnh_file, 'r', encoding='utf-8') as f:
    today_cnh_html = f.read()

# 使用BeautifulSoup解析HTML
soup_wsj = BeautifulSoup(wsj_html, 'html.parser')
soup_today_cnh = BeautifulSoup(today_cnh_html, 'html.parser')

# 找到两个文件中的表格
table_wsj = soup_wsj.find('table')
table_today_cnh = soup_today_cnh.find('table')

# 将wsj的表格内容加到today_cnh的表格末尾
for row in table_wsj.find_all('tr')[1:]:  # 跳过表头
    table_today_cnh.append(row)

# 将合并后的内容保存到一个新文件中
with open(today_cnh_file, 'w', encoding='utf-8') as f:
    f.write(str(soup_today_cnh))

print(f"合并后的文件已保存为: {today_cnh_file}")