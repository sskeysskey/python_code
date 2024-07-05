import os
import re
import shutil
from datetime import datetime

# 设置基本路径
base_path = "/Users/yanzhang/Downloads/"
backup_folder = "/Users/yanzhang/Movies/Caption_Backup/"

# 获取当前日期
current_date = datetime.now()
current_month = current_date.month
current_day = current_date.day

# 构造文件名
file_name = f"{current_month}月{current_day}日.srt"
file_path = os.path.join(base_path, file_name)

if not os.path.exists(file_path):
    # 读取文件内容
    with open(os.path.join(base_path, "bob.txt"), 'r', encoding='utf-8') as f:
        file1_lines = f.readlines()
    with open(os.path.join(base_path, "sub.srt"), 'r', encoding='utf-8') as f:
        file2_lines = f.readlines()

    # 初始化结果列表和索引
    result_lines = []
    file1_line_index = 0

    # 初始化结果列表和索引
    result_lines = []
    file1_line_index = 0

    # 合并文件内容
    for line in file2_lines:
        if line.strip() and re.search(r'[a-zA-Z]+', line):
            if file1_line_index < len(file1_lines):
                while file1_line_index < len(file1_lines) and not file1_lines[file1_line_index].strip():
                    file1_line_index += 1
                if file1_line_index < len(file1_lines):
                    result_lines.append(file1_lines[file1_line_index].rstrip() + '\n')
                    file1_line_index += 1
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)

    # 确保最后一行也有换行符
    if result_lines and not result_lines[-1].endswith('\n'):
        result_lines[-1] += '\n'

    # 保存结果到新文件
    temp_file = os.path.join(base_path, "temp.srt")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    # 重命名最终文件
    os.rename(temp_file, file_path)

    # 备份原始文件
    date_string = f"{current_month}月{current_day}日"
    for old_name, new_name in [("bob.txt", f"{date_string}_bob.txt"), ("sub.srt", f"{date_string}_sub.srt")]:
        old_path = os.path.join(base_path, old_name)
        new_path = os.path.join(backup_folder, new_name)
        shutil.move(old_path, new_path)

    print("处理完成。")
else:
    print("目标文件已存在，无需处理。")