import re
import os
import sys
import shutil
import pyperclip
import tkinter as tk
from tkinter.font import Font
from tkinter import filedialog

# 在 on_escape 函数中设置一个标志位
file_moved = False  # 全局变量，初始值为False

def on_escape(event=None):
    global file_moved
    file_moved = False  # 用户按下ESC，设置标志位为False
    root.destroy()

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 3) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

def on_split(event=None):
    global file_moved
    n_str = entry.get()
    if not n_str.isdigit():
        info_label.config(text="请输入有效的数字")
        return

    n = int(n_str)
    if n <= 0:
        info_label.config(text="请输入大于0的数字")
        return

    try:
        save_segments(n)
        info_label.config(text=f"分割完成，共分割成{n}部分")
        file_moved = True  # 分割成功，设置标志位为True
    except Exception as e:
        info_label.config(text=f"发生错误：{e}")
    finally:
        # 无论是否发生异常，都关闭Tkinter窗口
        root.destroy()  # 执行完毕后关闭窗口

# 新增的移动文件函数
def move_file_to_backup(file_path, destination_folder):
    # 获取文件名
    file_name = file_path.split('/')[-1]
    # 构造目标路径
    destination_path = f"{destination_folder}/{file_name}"
    try:
        # 移动文件
        shutil.move(file_path, destination_path)
        print(f"文件已移动到：{destination_path}")
    except Exception as e:
        # 如果出现异常，打印异常信息
        print(f"移动文件时发生错误：{e}")

def get_clipboard_size():
    text = pyperclip.paste()
    size_bytes = len(text.encode('utf-8'))
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def find_nearest_sentence_end(text, start, end):
    # 在指定范围内查找最近的句号位置
    dot_positions = [text.rfind('.\n', start, end), text.rfind('。\n', start, end)]
    # 过滤掉找不到的情况
    valid_positions = [pos for pos in dot_positions if pos != -1]

    if valid_positions:
        # 返回最近的一个句号位置
        return max(valid_positions)
    else:
        # 如果没有句号，返回原分割点
        return end

def split_text(text, n):
    segments = []
    segment_length = len(text) // n
    start = 0

    for _ in range(n - 1):
        end = start + segment_length
        if end >= len(text):
            end = len(text) - 1

        nearest_end = find_nearest_sentence_end(text, start, end)
        segments.append(text[start:nearest_end + 1])
        start = nearest_end + 1

    if start < len(text):
        segments.append(text[start:])

    return segments

def save_segments(n, save_path="/Users/yanzhang/Downloads/Travel_temp"):
    text = pyperclip.paste()
    segments = split_text(text, n)

    for i, segment in enumerate(segments):
        if segment:
            file_path = os.path.join(save_path, f'segment_{i + 1}.txt')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(segment)
            print(f"第{i + 1}部分已保存到: {file_path}")

# 正则表达式，匹配http://, https://或www.开头，直到空格或换行符的字符串
url_pattern = re.compile(
    r'([^ \n]*http[s]?://[^ \n]*(?=\s|$)|'
    r'[^ \n]*www\.[^ \n]*(?=\s|$)|'
    r'[^ \n]*E-mail[^ \n]*(?=\s|$)|'
    r'[^ \n]*\.(com|gov|edu|cn|us|html|htm|shtm|uk|xml|js|css|it)[^ \n]*(?=\s|$))'
)

# 初始化Tkinter，不显示主窗口
root = tk.Tk()
# root.withdraw()

# 弹出文件选择对话框，选择源文件
source_file_path = filedialog.askopenfilename(
    title='选择要处理的文件',
    filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
)

# 用户没有选择文件则退出
if not source_file_path:
    print('没有选择文件。')
    sys.exit()

# 读取文件内容
with open(source_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# 替换掉所有的URL链接
clean_content = re.sub(url_pattern, '', content)

# 将处理后的内容写入剪贴板
pyperclip.copy(clean_content)

root.title("分割文本")

# 设置字体
font = Font(family="Helvetica", size=24)

# 创建一个标签来显示剪贴板文本大小
clipboard_size_label = tk.Label(root, text=f"文本大小：{get_clipboard_size()}", font=font, anchor='w', justify='center')
clipboard_size_label.pack(pady=10, padx=10)

# 创建一个标签来显示信息，并设置字体和左对齐
info_label = tk.Label(root, text=f"需要分割成几份？", font=font, anchor='w', justify='center')
info_label.pack(pady=10, padx=10)

# 创建输入框
entry = tk.Entry(root, font=font)
entry.pack(pady=10, padx=30)
entry.focus()  # 让输入框获得焦点

# 绑定回车键到 on_split 函数
entry.bind('<Return>', on_split)  # 不需要 lambda 表达式

# 绑定 Esc 键到 on_escape 函数
root.bind('<Escape>', on_escape)

# 窗口居中
center_window(root)

# 提升窗口到最前
root.lift()
# 强制窗口获得焦点
root.focus_force()
# 让输入框获得焦点
entry.focus_set()

# 运行 Tkinter 事件循环
root.mainloop()

# 调用函数，移动文件
backup_folder = "/Users/yanzhang/Downloads/backup/TXT/Done"

# 在程序的最后部分，仅在 file_moved 为 True 时移动文件
if file_moved:  # 检查标志位是否为True
    move_file_to_backup(source_file_path, backup_folder)

# 在Tkinter事件循环结束后添加退出程序的调用
sys.exit()