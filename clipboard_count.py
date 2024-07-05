import re
import pyperclip
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

# 计算数字的数量
num_digits = len(re.findall(r'\d', clipboard_content))

# 计算不是英文字母（a-z，A-Z）、数字（0-9）或空格的字符数量
num_symbols = sum(not ch.isalnum() and not ch.isspace() for ch in clipboard_content)

# 计算所有行数
num_lines_all = clipboard_content.count('\n') + 1  # 假定内容至少有一行

# 计算无空行行数
num_lines_pure = sum(1 for line in clipboard_content.splitlines() if line.strip())

# 创建 Tkinter 窗口
root = tk.Tk()
root.title("剪贴板分析")

# 设置字体喽
font = Font(family="Helvetica", size=24)

# 创建 Text 控件来显示信息，并设置字体
text_widget = tk.Text(root, font=font, height=15, width=15)
text_widget.pack(pady=10, padx=10)

# 定义不同类型文本的颜色标签
text_widget.tag_configure('total_color', foreground='red')
text_widget.tag_configure('chinese_color', foreground='yellow')
text_widget.tag_configure('english_color', foreground='orange')
text_widget.tag_configure('symbol_color', foreground='green')  # 符号的颜色标签
text_widget.tag_configure('line_color', foreground='orange')  # 行数的颜色标签
text_widget.tag_configure('digit_color', foreground='white')  # 数字数量的颜色标签

# 插入文本并设置样式
text_widget.insert('end', f"总共字符： {total_characters}\n\n", 'total_color')
text_widget.insert('end', f"中文字： {num_chinese_characters}\n\n", 'chinese_color')
text_widget.insert('end', f"英文单词： {num_english_words}\n\n", 'english_color')
text_widget.insert('end', f"数字数量： {num_digits}\n\n", 'digit_color')  # 应用数字数量的颜色标签
text_widget.insert('end', f"符号数量： {num_symbols}\n\n", 'symbol_color')  # 应用符号的颜色标签
text_widget.insert('end', f"总行数： {num_lines_all}\n\n", 'line_color')  # 应用行数的颜色标签
text_widget.insert('end', f"除空行行数： {num_lines_pure}\n\n", 'line_color')  # 应用行数的颜色标签

# 禁止 Text 控件的编辑功能
text_widget.config(state='disabled')

# 绑定 Esc 键到 on_escape 函数
root.bind('<Escape>', on_escape)

# 窗口居中
center_window(root)

# 运行 Tkinter 事件循环
root.mainloop()