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

    # 找到所有日期项
    date_cells = soup.find_all('td')

    # 移除两天前的内容并准备写入备份文件的内容
    backup_content = ''
    for date_cell in date_cells:
        date_str = date_cell.get_text().strip()
        # 尝试提取和转换日期字符串
        try:
            article_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            # 检查日期是否是一天前
            if article_date <= previous_day:
                parent_row = date_cell.find_parent('tr')
                if parent_row:
                    backup_content += str(parent_row) + '\n'
                    parent_row.decompose()
        except ValueError:
            continue  # 解析失败则跳过当前循环

    # 将修改后的内容写回源文件
    with open(source_file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    # 处理备份文件
    if backup_content:
        # 如果备份文件不存在，或者为新文件，则添加头部
        if not os.path.isfile(backup_file_path) or os.path.getsize(backup_file_path) == 0:
            with open(backup_file_path, 'w', encoding='utf-8') as file:
                file.write('<html>\n<head><title>Backup</title>\n')
                file.write(css_styles)
                file.write('</head>\n<body>\n<table>\n')
                file.write('<tr><th>时间</th><th>摘要</th></tr>\n')
                file.write(backup_content)
                file.write('</table>\n</body>\n</html>')
        else:
            # 如果备份文件已存在，追加新的备份内容
            with open(backup_file_path, 'a', encoding='utf-8') as file:
                file.write(backup_content)