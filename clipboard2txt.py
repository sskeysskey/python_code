# save_clipboard_to_srt.py
import pyperclip

# 设置SRT文件的保存路径
srt_file_path = '/Users/yanzhang/Documents/eating_animals_cn.txt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 追加剪贴板内容到SRT文件
with open(srt_file_path, 'a', encoding='utf-8-sig') as f:
    f.write(clipboard_content)