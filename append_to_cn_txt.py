# append_to_cn_files.py
import os
import pyperclip

# 设置目录路径测试
directory = '/Users/yanzhang/'
keyword = 'cn'
file_extension = '.txt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 在目录中搜索包含关键字的文件
files_found = [f for f in os.listdir(directory) if keyword in f and f.endswith(file_extension)]

# 如果找到文件，则追加内容
for filename in files_found:
    file_path = os.path.join(directory, filename)
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(clipboard_content)