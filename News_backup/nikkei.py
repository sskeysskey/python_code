from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# 定义文件路径
source_file_path = '/Users/yanzhang/Documents/sskeysskey.github.io/news/nikkei.html'
backup_file_path = '/Users/yanzhang/Documents/sskeysskey.github.io/news/nikkei_backup.html'

# 定义两天前的日期
previous_day = datetime.now() - timedelta(days=3)
print(f"Previous day is set to: {previous_day}")

# 读取源文件内容
with open(source_file_path, 'r', encoding='utf-8') as file:
    content = file.read()
    soup = BeautifulSoup(content, 'html.parser')

# 找到所有日期项
date_cells = soup.find_all('td')

# 移除两天前的内容并准备写入备份文件的内容
backup_content = ''
for date_cell in date_cells:
    date_str = date_cell.get_text().strip() # 删除可能的前后空格
    print(f"Found date string: {date_str}")  # 输出找到的日期字符串
    # 尝试提取和转换日期字符串
    try:
        article_date = datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Error parsing date: {e}")  # 打印错误信息
        continue  # 解析失败则跳过当前循环

    # 检查日期是否是两天前
    if article_date <= previous_day:
        print(f"Article from {article_date} will be moved to backup.")  # 输出将要移动到备份的文章日期
        parent_row = date_cell.find_parent('tr')
        if parent_row:
            backup_content += str(parent_row) + '\n'
            parent_row.decompose()

# 检查备份文件是否存在，如果不存在则创建并添加HTML结构标签
if not os.path.exists(backup_file_path):
    with open(backup_file_path, 'w', encoding='utf-8') as file:
        file.write('<html>\n<head><title>Backup</title></head>\n<body>\n<table>\n')
        file.write('<tr><th>时间</th><th>摘要</th></tr>\n')  # 添加表头

# 将修改后的内容写回源文件
with open(source_file_path, 'w', encoding='utf-8') as file:
    file.write(str(soup))

# 如果有备份内容，则追加到备份文件
if backup_content:
    with open(backup_file_path, 'a', encoding='utf-8') as file:
        file.write(backup_content)

# 如果是首次创建备份文件（即之前没有备份内容），则关闭HTML标签
if not os.path.exists(backup_file_path) or os.path.getsize(backup_file_path) == 0:
    with open(backup_file_path, 'a', encoding='utf-8') as file:
        file.write('</table>\n</body>\n</html>')