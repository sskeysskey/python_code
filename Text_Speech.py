import os
import sys
import tkinter as tk
from tkinter import filedialog

# 初始化Tkinter，不显示主窗口
root = tk.Tk()
root.withdraw()

# 弹出文件选择对话框，选择源文件
source_file_path = filedialog.askopenfilename(
    title='选择要处理的文件',
    filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
)

# 用户没有选择文件则退出
if not source_file_path:
    print('没有选择文件。')
    sys.exit()

# 获取源文件的原始文件名
source_file_name = os.path.basename(source_file_path)

# 去除文件名中的空格
cleaned_file_name = source_file_name.replace(' ', '')

# 去除文件名的扩展名
cleaned_file_name_without_extension = os.path.splitext(cleaned_file_name)[0]

# 在/tmp目录下创建mp3name.txt文件，并写入处理后的文件名
mp3name_path = "/tmp/mp3name.txt"
with open(mp3name_path, 'w', encoding='utf-8') as mp3name_file:
    mp3name_file.write(cleaned_file_name_without_extension)

print(f"文件名已保存到: {mp3name_path}")

# 读取文件内容
with open(source_file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 初始化变量
current_length = 0
max_length = 2600  # 最大字符数
part_num = 1
part_lines = []

def write_part_file(part_num, part_lines):
    directory = "/tmp/"
    part_file_path = os.path.join(directory, f"textspeech_{part_num}.txt")
    with open(part_file_path, 'w', encoding='utf-8') as part_file:
        part_file.writelines(part_lines)
    print(f"生成文件: {part_file_path}")

# 逐行读取，并在句号后截断
for line in lines:
    sentences = line.split('。')
    for i, sentence in enumerate(sentences):
        if sentence:
            sentence_with_period = sentence + '。' if i < len(sentences) - 1 else sentence
            if current_length + len(sentence_with_period) > max_length:
                write_part_file(part_num, part_lines)
                part_num += 1
                part_lines = []
                current_length = 0
            part_lines.append(sentence_with_period)
            current_length += len(sentence_with_period)

# 写入最后一个部分
if part_lines:
    write_part_file(part_num, part_lines)

print("文件切割完成。")