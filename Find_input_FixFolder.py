import os
import sys
import json
import subprocess
import threading
from tkinter import Tk, Text, Scrollbar, Button, Entry, Label, Toplevel

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
    # "/Users/yanzhang/Documents/Books",
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
    input_window_width = 300
    input_window_height = 100
    window_center(input_window, input_window_width, input_window_height, 100)

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

def search_json_for_keywords(json_path, keywords):
    with open(json_path, 'r') as file:
        data = json.load(file)
    matched_names_stocks = []
    matched_names_etfs = []
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    # 搜索 stocks 分类
    for stock in data.get('stocks', []):
        # 合并描述和标签为一个大的搜索文本
        combined_text = ' '.join([stock['description1'], stock['description2']] + stock.get('tag', []))
        combined_text = combined_text.lower()
        # 检查是否所有关键词都在合并后的文本中
        if all(keyword in combined_text for keyword in keywords_lower):
            matched_names_stocks.append(stock['name'])

    # 搜索 etfs 分类
    for etf in data.get('etfs', []):
        # 同样合并描述和标签
        combined_text = ' '.join([etf['description1'], etf['description2']] + etf.get('tag', []))
        combined_text = combined_text.lower()
        # 检查是否所有关键词都在合并后的文本中
        if all(keyword in combined_text for keyword in keywords_lower):
            matched_names_etfs.append(etf['name'])

    return matched_names_stocks, matched_names_etfs

def show_results_with_json(results, json_path, keywords):
    matched_names_stocks, matched_names_etfs = search_json_for_keywords(json_path, keywords)

    result_window = Toplevel(root)
    result_window.title("搜索结果")
    window_center(result_window, 800, 600)
    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side="right", fill="y")
    text = Text(result_window, width=120, height=25, yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both")
    text.tag_configure('directory_tag', foreground='yellow', font=('Helvetica', '24', 'bold'))
    text.tag_configure('file_tag', foreground='orange', underline=True, font=('Helvetica', '20'))
    text.tag_configure('stock_tag', foreground='purple', underline=True, font=('Helvetica', '20'))
    text.tag_configure('etf_tag', foreground='green', underline=True, font=('Helvetica', '20'))
    scrollbar.config(command=text.yview)
    result_window.bind('<Escape>', lambda e: (result_window.destroy(), sys.exit(0)))

    def open_file_and_change_tag_color(path, tag_name):
        open_file(path)
        text.tag_configure(tag_name, foreground='grey', underline=False)

    def open_json_file(tag_name):
        open_file(json_path)
        text.tag_configure(tag_name, foreground='grey', underline=False)

    if results:
        for directory, files in results.items():
            if files:
                text.insert("end", directory + "\n", 'directory_tag')
                for file in files:
                    file_path = os.path.join(directory, file)
                    tag_name = "link_" + file.replace(".", "_")
                    text.tag_bind(tag_name, "<Button-1>", lambda event, path=file_path, tag=tag_name: open_file_and_change_tag_color(path, tag))
                    text.insert("end", file + "\n", (tag_name, 'file_tag'))
                text.insert("end", "\n")
    else:
        text.insert("end", "没有找到包含关键词的文件。\n")

    if matched_names_stocks:
        text.insert("end", "匹配的股票名称:\n", 'directory_tag')
        for name in matched_names_stocks:
            tag_name = "stock_" + name.replace(" ", "_")
            text.tag_bind(tag_name, "<Button-1>", lambda event, tag=tag_name: open_json_file(tag))
            text.insert("end", name + "\n", (tag_name, 'stock_tag'))

    if matched_names_etfs:
        text.insert("end", "匹配的ETFs名称:\n", 'directory_tag')
        for name in matched_names_etfs:
            tag_name = "etf_" + name.replace(" ", "_")
            text.tag_bind(tag_name, "<Button-1>", lambda event, tag=tag_name: open_json_file(tag))
            text.insert("end", name + "\n", (tag_name, 'etf_tag'))

def threaded_search_files_with_json(directories, keywords, json_path, callback):
    results = search_files(directories, keywords)
    root.after(0, callback, results, json_path, keywords)

json_path = "/Users/yanzhang/Documents/Financial_System/Modules/Description.json"
custom_input_window("请输入要检索的字符串内容：", 
                    lambda keyword: threading.Thread(target=threaded_search_files_with_json, args=(searchFolders, keyword, json_path, show_results_with_json)).start())

root.mainloop()