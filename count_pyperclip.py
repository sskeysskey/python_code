import pyperclip
import re
import tkinter as tk
from tkinter.font import Font

def on_escape(event=None):
    root.destroy()

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 3) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

# 获取剪贴板内容
clipboard_content = pyperclip.paste()

# 计算剪贴板内容的总字符数量
total_characters = len(clipboard_content)

# 计算中文字符的数量
num_chinese_characters = len(re.findall(r'[\u4e00-\u9fff]', clipboard_content))

# 计算英文单词的数量
num_english_words = len(re.findall(r'\b[A-Za-z]+\b', clipboard_content))

# 计算不是英文字母（a-z，A-Z）、数字（0-9）或空格的字符数量
num_symbols = sum(not ch.isalnum() and not ch.isspace() for ch in clipboard_content)

# 创建 Tkinter 窗口
root = tk.Tk()
root.title("剪贴板分析")

# 设置字体
font = Font(family="Helvetica", size=24)

# 创建一个标签来显示信息，并设置字体和左对齐
info_label = tk.Label(root, text=f"总共字符： {total_characters}\n\n中文字符： {num_chinese_characters}\n\n英文单词： {num_english_words}\n\n符号数量： {num_symbols}", font=font, anchor='w', justify='left')
info_label.pack(pady=30, padx=60)

# 绑定 Esc 键到 on_escape 函数
root.bind('<Escape>', on_escape)

# 窗口居中
center_window(root)

# 运行 Tkinter 事件循环
root.mainloop()
