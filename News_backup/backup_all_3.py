from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# 定义文件路径
source_dir_path = '/Users/yanzhang/Documents/sskeysskey.github.io/news'

# 定义目标文件列表
target_files = [
    "economist.html",
    "FT.html",
    "nikkei.html",
    "nytimes.html",
    "technologyreview.html",
    "wsj.html"
]

# 定义CSS样式
css_styles = """
<style>
table {
    border-collapse: collapse;
}
th, td {
    border: 1px solid #009879; /* 边框颜色 */
    padding: 8px;
    text-align: left;
    font-size: 16px; /* 字体大小 */
}
</style>
"""

# 定义两天前的日期
previous_day = datetime.now() - timedelta(days=1)
print(f"Previous day is set to: {previous_day}")

# 处理特定的文件
for file_name in target_files:
    # 构造完整的源文件和备份文件路径
    source_file_path = os.path.join(source_dir_path, file_name)
    backup_file_path = os.path.join(source_dir_path, file_name.replace('.html', '_backup.html'))

    # 读取源文件内容
    with open(source_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        soup = BeautifulSoup(content, 'html.parser')

    backup_content = ''
    for date_cell in soup.find_all('td'):
        try:
            date_text = date_cell.get_text().strip()
            article_date = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
            if article_date <= previous_day:
                parent_row = date_cell.find_parent('tr')
                backup_content += str(parent_row) + '\n'
                parent_row.decompose()
        except ValueError:
            continue

    # 写回修改后的HTML到原始文件
    with open(source_file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    # 如果有要备份的内容
    if backup_content:
        # 检查备份文件是否存在，不存在则创建
        if not os.path.exists(backup_file_path):
            with open(backup_file_path, 'w', encoding='utf-8') as bfile:
                #bfile.write('<html><head><title>Backup</title></head><body><table>\n')
                file.write('<html>\n<head><title>Backup</title>\n')
                file.write(css_styles)
                file.write('</head>\n<body>\n<table>\n')
                bfile.write('<tr><th>时间</th><th>摘要</th></tr>\n')

        # 追加内容到备份文件
        with open(backup_file_path, 'a', encoding='utf-8') as bfile:
            bfile.write(backup_content)
        
        # 确保备份文件的HTML闭合
        with open(backup_file_path, 'a', encoding='utf-8') as bfile:
            bfile.write('</table></body></html>')