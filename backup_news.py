import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 确保CSS样式被包含在备份文件中的函数
def ensure_css_in_backup(file_path, css_styles):
    with open(file_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        # 检查是否已经包含CSS样式
        if '<style>' not in content:
            # 如果没有，则在<body>标签之前插入CSS样式
            content = content.replace('<body>', f'<head><title>Backup</title>\n{css_styles}</head>\n<body>')
            file.seek(0)
            file.write(content)
            file.truncate()  # 删除旧内容后面的部分

# 定义文件路径
source_dir_path = '/Users/yanzhang/Documents/sskeysskey.github.io/news'
backup_dir_path = '/Users/yanzhang/Documents/sskeysskey.github.io/news/backup'

# 定义目标文件列表
target_files = [
    "economist.html",
    "nikkei.html",
    "nytimes.html",
    "bloomberg.html",
    "hbr.html",
    "technologyreview.html"
]

# 定义CSS样式
css_styles = """
<style>
    body {
        font-size: 28px; /* 设置字体大小 */
    }
    table {
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #000; /* 加粗整个表格的外边框 */
        box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2); /* 增加阴影效果 */
    }
    th, td {
        padding: 10px;
        text-align: left;
        border-bottom: 2px solid #000;
        border-right: 2px solid #000; /* 增加垂直分割线 */
    }
    th {
        background-color: #f2f2f2; /* 表头背景色 */
        font-weight: bold; /* 表头字体加粗 */
    }
    tr:hover {
        background-color: #f5f5f5; /* 鼠标悬浮时行背景色变化 */
    }
    tr:last-child td {
        border-bottom: 2px solid #000; /* 最后一行的底部边框加粗 */
    }
    td:last-child, th:last-child {
        border-right: none; /* 最后一列去除垂直分割线 */
    }
</style>
"""

# 处理特定的文件
for file_name in target_files:
    # 构造完整的源文件和备份文件路径
    source_file_path = os.path.join(source_dir_path, file_name)
    backup_file_path = os.path.join(backup_dir_path, file_name.replace('.html', '_backup.html'))

    # 根据文件名设置日期阈值
    if file_name == 'technologyreview.html':
        previous_day = datetime.now() - timedelta(days=30)
    else:
        previous_day = datetime.now() - timedelta(days=3)
    print(f"处理文件: {file_name}, 使用日期阈值: {previous_day}")
    
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
                file.write('<!DOCTYPE html>\n<html>\n')
                file.write('<head>\n<title>Backup</title>\n')
                file.write(css_styles)  # 确保CSS样式被添加到<head>标签内
                file.write('</head>\n<body>\n<table>\n')
                file.write('<tr><th>时间</th><th>摘要</th></tr>\n')
                file.write(backup_content)
                file.write('</table>\n</body>\n</html>')
        else:
            # 如果备份文件已存在，确保CSS样式存在
            ensure_css_in_backup(backup_file_path, css_styles)
            # 追加新的备份内容
            with open(backup_file_path, 'a', encoding='utf-8') as file:
                file.write(backup_content)