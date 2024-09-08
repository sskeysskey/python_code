import os
import re
import shutil
import subprocess
from datetime import datetime

# 设置基本路径
base_path = "/Users/yanzhang/Downloads/"
backup_folder = "/Users/yanzhang/Movies/Caption_Backup/"

def find_bob_file(base_path):
    bob_pattern = re.compile(r'bob', re.IGNORECASE)
    for file in os.listdir(base_path):
        if file.endswith('.txt') and bob_pattern.search(file):
            return file
    return None

def count_valid_lines(file_path, is_bob_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        if is_bob_file:
            return sum(1 for line in f if line.strip())
        else:
            return sum(1 for line in f if line.strip() and re.search(r'[a-zA-Z]', line))

def display_dialog(message):
    applescript_code = f'display dialog "{message}" buttons {{"OK"}} default button "OK"'
    subprocess.run(['osascript', '-e', applescript_code], check=True)

# 删除以 "concatenated" 开头的 PNG 文件
for file in os.listdir(base_path):
    if file.startswith("concatenated") and file.endswith(".png"):
        os.remove(os.path.join(base_path, file))

# 获取当前日期
current_date = datetime.now()
current_month = current_date.month
current_day = current_date.day

# 构造文件名
file_name = f"{current_month}月{current_day}日.srt"
file_path = os.path.join(base_path, file_name)

if not os.path.exists(file_path):
    # 查找以Bob开头的txt文件或bob.txt
    bob_file = find_bob_file(base_path)

    if not bob_file:
        print("未找到以Bob开头的txt文件或bob.txt，处理终止。")
        exit()
    
    # 查找目录下的第一个srt文件
    srt_file = next((f for f in os.listdir(base_path) if f.endswith(".srt")), None)
    
    if not srt_file:
        print("未找到srt文件，处理终止。")
        exit()

    # 计算有效行数
    bob_lines = count_valid_lines(os.path.join(base_path, bob_file), True)
    srt_lines = count_valid_lines(os.path.join(base_path, srt_file), False)

    if bob_lines != srt_lines:
        display_dialog(f"文件行数不匹配：Bob文件有 {bob_lines} 行，SRT文件有 {srt_lines} 行有效内容。")
        exit()

    # 读取文件内容
    with open(os.path.join(base_path, bob_file), 'r', encoding='utf-8') as f:
        file1_lines = f.readlines()
    with open(os.path.join(base_path, srt_file), 'r', encoding='utf-8') as f:
        file2_lines = f.readlines()

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
    for old_name, new_name in [(bob_file, f"{date_string}_{bob_file}"), (srt_file, f"{date_string}_{srt_file}")]:
        old_path = os.path.join(base_path, old_name)
        new_path = os.path.join(backup_folder, new_name)
        shutil.move(old_path, new_path)

    print(f"处理完成。使用的文件: {bob_file} 和 {srt_file}")
else:
    print("目标文件已存在，无需处理。")