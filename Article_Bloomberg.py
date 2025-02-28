import os
import pyperclip

file_path = '/tmp/article_bloomberg.txt'

if os.path.exists(file_path):
    # 文件存在,读取内容到剪贴板
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pyperclip.copy(content)
    
    # 删除文件
    os.remove(file_path)
    print('文件内容已复制到剪贴板并删除文件')
else:
    # 文件不存在,获取剪贴板内容并写入文件
    content = pyperclip.paste()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('剪贴板内容已写入文件')