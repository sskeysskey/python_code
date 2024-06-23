import re
import os
import sys
import shutil
import pyperclip
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.font import Font

# 全局变量
file_moved = False

def on_escape(event=None):
    global file_moved
    file_moved = False
    root.destroy()

def center_window(win):
    win.update_idletasks()
    width, height = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 3) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

def on_split(event=None):
    global file_moved
    try:
        n = int(entry.get())
        if n <= 0:
            raise ValueError("请输入大于0的数字")
        save_segments(n)
        info_label.config(text=f"分割完成，共分割成{n}部分")
        file_moved = True
    except ValueError as ve:
        info_label.config(text=str(ve))
    except Exception as e:
        info_label.config(text=f"发生错误：{e}")
    finally:
        root.destroy()

def move_file_to_backup(file_path, destination_folder):
    try:
        shutil.move(file_path, os.path.join(destination_folder, os.path.basename(file_path)))
        print(f"文件已移动到：{destination_folder}")
    except Exception as e:
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

def find_nearest_sentence_end(text, start, ideal_end):
    positions = [
        text.rfind('.\n', start, ideal_end),
        text.rfind('。\n', start, ideal_end),
        text.find('.\n', ideal_end),
        text.find('。\n', ideal_end)
    ]
    valid_positions = [pos for pos in positions if pos != -1]
    return min(valid_positions, key=lambda pos: abs(pos - ideal_end)) if valid_positions else ideal_end

def split_text(text, n):
    segments, start = [], 0
    ideal_segment_length = len(text) // n

    for _ in range(n - 1):
        ideal_end = min(start + ideal_segment_length, len(text) - 1)
        nearest_end = find_nearest_sentence_end(text, start, ideal_end)
        segments.append(text[start:nearest_end + 1])
        start = nearest_end + 1

    segments.append(text[start:])
    return segments

def save_segments(n, save_path="/Users/yanzhang/Downloads/backup/TXT/Segments/"):
    text = pyperclip.paste()
    segments = split_text(text, n)

    os.makedirs(save_path, exist_ok=True)
    for i, segment in enumerate(segments):
        with open(os.path.join(save_path, f'segment_{i + 1}.txt'), 'w', encoding='utf-8') as file:
            file.write(segment)
        print(f"第{i + 1}部分已保存到: {save_path}")

def contains_segment(filename, segment):
    return segment in filename

def check_for_existing_segments(directory, segment):
    return any(file.endswith('.txt') and contains_segment(file, segment) for file in os.listdir(directory))

url_pattern = re.compile(
    r'(?:\s|^)([^ \n]*http[s]?://[^ \n]*(?=\s|$)|'
    r'[^ \n]*www\.[^ \n]*(?=\s|$)|'
    r'[^ \n]*E-mail[^ \n]*(?=\s|$)|'
    r'[^ \n]*\.(com|gov|org|edu|cn|us|html|htm|shtm|uk|xml|js|css|it)[^ \n]*(?=\s|$)|'
    r'[^ \n]+\.[^ \n]+\.[^ \n]+)(?=\s|$)'
)

save_path = "/Users/yanzhang/Downloads/backup/TXT/Segments/"

if check_for_existing_segments(save_path, 'segment'):
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("警告", "目录segments中存在包含'segment'的txt文件，请先处理好现有文件。")
    sys.exit()

root = tk.Tk()
source_file_path = filedialog.askopenfilename(title='选择要处理的文件', filetypes=[('Text files', '*.txt'), ('All files', '*.*')])

if not source_file_path:
    print('没有选择文件。')
    sys.exit()

with open(source_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

clean_content = re.sub(url_pattern, '', content)
pyperclip.copy(clean_content)

root.title("分割文本")
font = Font(family="Helvetica", size=24)

clipboard_size_label = tk.Label(root, text=f"文本大小：{get_clipboard_size()}", font=font)
clipboard_size_label.pack(pady=10, padx=10)

info_label = tk.Label(root, text="需要分割成几份？", font=font)
info_label.pack(pady=10, padx=10)

entry = tk.Entry(root, font=font)
entry.pack(pady=10, padx=30)
entry.focus()

entry.bind('<Return>', on_split)
root.bind('<Escape>', on_escape)

center_window(root)
root.lift()
root.focus_force()
entry.focus_set()

root.mainloop()

if 'segment' not in os.path.basename(source_file_path):
    new_file_directory = "/Users/yanzhang/Documents/"
    new_file_path = os.path.join(new_file_directory, os.path.basename(source_file_path))

    try:
        os.makedirs(new_file_directory, exist_ok=True)
        with open(new_file_path, 'x', encoding='utf-8'):
            pass
        print(f"在 {new_file_directory} 下创建了同名空txt文件：{os.path.basename(source_file_path)}")
    except FileExistsError:
        print(f"文件已存在：{new_file_path}")
    except Exception as e:
        print(f"创建文件时发生错误：{e}")
else:
    print('文件名中包含"segment"，不创建空文件。')

backup_folder = "/Users/yanzhang/Downloads/backup/TXT/Done"

if file_moved:
    if contains_segment(os.path.basename(source_file_path), 'segment'):
        os.remove(source_file_path)
        print(f"文件包含'segment'，已被删除：{source_file_path}")
    else:
        move_file_to_backup(source_file_path, backup_folder)

sys.exit()