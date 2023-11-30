# save_clipboard_to_srt.py
import pyperclip

# 设置SRT文件的保存路径
srt_file_path = '/Users/yanzhang/Movies/subtitles.srt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 追加剪贴板内容到SRT文件，并在最后添加一个空行
with open(srt_file_path, 'a', encoding='utf-8-sig') as f:
    f.write(clipboard_content)
    f.write('\n\n')  # 添加两个换行符以创建一个空行