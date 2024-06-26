import os
import sys
import json
import pyperclip
import subprocess
import threading
from tkinter import Tk, Text, Scrollbar, Button, Entry, Label, Toplevel
import tkinter as tk

# 初始化Tkinter，隐藏主窗口
root = Tk()
root.withdraw()

# 固定的搜索目录列表
searchFolders = [
    "/Users/yanzhang/Documents/ScriptEditor/",
    "/Users/yanzhang/Library/Services/",
    "/Users/yanzhang/Documents/Financial_System",
    "/Users/yanzhang/Documents/python_code",
    "/Users/yanzhang/Documents/News/backup"
    # "/Users/yanzhang/Documents/LuxuryBox",
    # "/Users/yanzhang/Documents/sskeysskey.github.io",
    # "/Users/yanzhang/Downloads/backup/TXT",
    # "/Users/yanzhang/Documents/Books"
]

def window_center(win, width, height, offset_y=0):
    screen_width, screen_height = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (screen_width - width) // 2, (screen_height - height) // 2 - offset_y
    win.geometry(f'{width}x{height}+{x}+{y}')

def open_file(file_path):
    try:
        subprocess.call(["open", file_path])
    except Exception as e:
        print(f"无法打开文件 {file_path}: {e}")

def custom_input_window(prompt, callback):
    input_window = Toplevel(root)
    input_window.title("输入")
    window_center(input_window, 300, 100, 100)

    def on_ok():
        keyword = entry.get()
        input_window.destroy()
        callback(keyword)

    def on_cancel():
        input_window.destroy()
        sys.exit(0)

    def on_esc(event):
        on_cancel()

    def on_enter(event):
        on_ok()

    Label(input_window, text=prompt).pack()
    entry = Entry(input_window)
    entry.pack()
    entry.focus_set()

    try:
        clipboard_content = root.clipboard_get()
    except tk.TclError:
        clipboard_content = ''
    entry.insert(0, clipboard_content)
    entry.select_range(0, tk.END)

    Button(input_window, text="取消", command=on_cancel).pack(side="right")
    Button(input_window, text="确定", command=on_ok).pack(side="right")

    entry.bind('<Return>', on_enter)
    input_window.bind('<Escape>', on_esc)

def search_files(directories, keywords):
    matched_files = {}
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    for directory in directories:
        matched_files[directory] = []
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                if dir_name.endswith('.workflow'):
                    handle_workflow_dir(root, dir_name, directory, keywords_lower, matched_files)
            for name in files:
                handle_file(root, name, directory, keywords_lower, matched_files)

    return matched_files

def handle_workflow_dir(root, dir_name, directory, keywords_lower, matched_files):
    workflow_path = os.path.join(root, dir_name)
    try:
        wflow_path = os.path.join(workflow_path, 'contents/document.wflow')
        with open(wflow_path, 'r') as file:
            content = file.read().lower()
        if all(keyword_lower in content for keyword_lower in keywords_lower):
            matched_files[directory].append(os.path.relpath(workflow_path, directory))
    except Exception as e:
        print(f"Error reading {wflow_path}: {e}")

def handle_file(root, name, directory, keywords_lower, matched_files):
    item_path = os.path.join(root, name)
    if item_path.endswith('.scpt'):
        try:
            content = subprocess.check_output(['osadecompile', item_path], text=True).lower()
            if all(keyword_lower in content for keyword_lower in keywords_lower):
                matched_files[directory].append(os.path.relpath(item_path, directory))
        except Exception as e:
            print(f"Error decompiling {item_path}: {e}")
    elif item_path.endswith(('.txt', '.py', '.json', '.js', '.css', '.html', '.csv', '.md')):
        try:
            with open(item_path, 'r') as file:
                content = file.read().lower()
            if all(keyword_lower in content for keyword_lower in keywords_lower):
                matched_files[directory].append(os.path.relpath(item_path, directory))
        except Exception as e:
            print(f"Error reading {item_path}: {e}")

def read_file_content(path):
    if path.endswith('.scpt'):
        return subprocess.check_output(['osadecompile', path], text=True).lower()
    with open(path, 'r') as file:
        return file.read().lower()

def search_json_for_keywords(json_path, keywords):
    with open(json_path, 'r') as file:
        data = json.load(file)
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    def search_category(category):
        return [
            item['symbol'] for item in data.get(category, [])
            if all(keyword in ' '.join([item['description1'], item['description2']]).lower() for keyword in keywords_lower)
        ]

    return search_category('stocks'), search_category('etfs')

def search_tag_for_keywords(json_path, keywords):
    with open(json_path, 'r') as file:
        data = json.load(file)
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    def search_category_for_tag(category):
        return [
            item['symbol'] for item in data.get(category, [])
            if all(keyword in ' '.join(item.get('tag', [])).lower() for keyword in keywords_lower)
        ]

    def search_category_for_name(category):
        return [
            item['symbol'] for item in data.get(category, [])
            if all(keyword in item['name'].lower() for keyword in keywords_lower)
        ]

    return (
        search_category_for_tag('stocks'), search_category_for_tag('etfs'),
        search_category_for_name('stocks'), search_category_for_name('etfs')
    )

def show_results_with_json(results, json_path, keywords):
    matched_names_stocks, matched_names_etfs = search_json_for_keywords(json_path, keywords)
    matched_names_stocks_tag, matched_names_etfs_tag, matched_names_stocks_name, matched_names_etfs_name = search_tag_for_keywords(json_path, keywords)

    result_window = Toplevel(root)
    result_window.title(f"搜索关键字: {keywords}")
    window_center(result_window, 800, 600)

    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side="right", fill="y")
    text = Text(result_window, width=120, height=25, yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both")
    text.tag_configure('directory_tag', foreground='yellow', font=('Helvetica', '24', 'bold'))
    text.tag_configure('file_tag', foreground='orange', underline=True, font=('Helvetica', '20'))
    text.tag_configure('tag1', foreground='gray', underline=True, font=('Helvetica', '20'))
    text.tag_configure('tag2', foreground='white', underline=True, font=('Helvetica', '20'))
    scrollbar.config(command=text.yview)
    result_window.bind('<Escape>', lambda e: (result_window.destroy(), sys.exit(0)))

    def open_file_and_change_tag_color(path, tag_name):
        open_file(path)
        text.tag_configure(tag_name, foreground='grey', underline=False)

    def insert_results(category, results, tag):
        if results:
            text.insert("end", f"{category}:\n", 'directory_tag')
            for name in results:
                text.insert("end", name + "\n", tag)
            text.insert("end", "\n")

    for directory, files in results.items():
        if files:
            text.insert("end", directory + "\n", 'directory_tag')
            for file in files:
                file_path = os.path.join(directory, file)
                tag_name = "link_" + file.replace(".", "_")
                # text.tag_bind(tag_name, "<Button-1>", lambda event, path=file_path, tag=tag_name: open_file(path))
                text.tag_bind(tag_name, "<Button-1>", lambda event, path=file_path, tag=tag_name: open_file_and_change_tag_color(path, tag))
                text.insert("end", file + "\n", (tag_name, 'file_tag'))
            text.insert("end", "\n")
        else:
            text.insert("end", "")

    insert_results("Stock_tag", matched_names_stocks_tag, 'tag2')
    insert_results("ETF_tag", matched_names_etfs_tag, 'tag2')
    insert_results("Stock_name", matched_names_stocks_name, 'tag2')
    insert_results("ETF_name", matched_names_etfs_name, 'tag2')
    insert_results("Description_Stock", matched_names_stocks, 'tag1')
    insert_results("Description_ETFs", matched_names_etfs, 'tag1')

def threaded_search_files_with_json(directories, keywords, json_path, callback):
    results = search_files(directories, keywords)
    root.after(0, callback, results, json_path, keywords)

def search_with_clipboard_content():
    clipboard_content = pyperclip.paste()
    if clipboard_content:
        threading.Thread(target=threaded_search_files_with_json, args=(searchFolders, clipboard_content, json_path, show_results_with_json)).start()
    else:
        print("剪贴板为空，请复制一些文本后再试。")

json_path = "/Users/yanzhang/Documents/Financial_System/Modules/Description.json"

if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == "input":
        custom_input_window("请输入要检索的字符串内容：", 
                           lambda keyword: threading.Thread(target=threaded_search_files_with_json, args=(searchFolders, keyword, json_path, show_results_with_json)).start())
    elif arg == "paste":
        search_with_clipboard_content()
else:
    print("请提供参数 input 或 paste")
    sys.exit(1)

root.mainloop()