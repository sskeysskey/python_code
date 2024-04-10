import os
import sys
import subprocess
from tkinter import Tk, Text, Scrollbar, Button, Entry, Label, Toplevel

# 初始化Tkinter，隐藏主窗口
root = Tk()
root.withdraw()

# 固定的搜索目录列表
searchFolders = [
    "/Users/yanzhang/Documents/ScriptEditor/",
    "/Users/yanzhang/Library/Services/",
    "/Users/yanzhang/Movies/Windows 11/",
    "/Users/yanzhang/Documents/python_code",
    "/Users/yanzhang/Documents/News/",
    "/Users/yanzhang/Documents/Books"
]

def window_center1(win, width, height):
    # 获取屏幕宽度和高度
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    # 计算窗口位置
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2 - 100)
    # 设置窗口大小和位置
    win.geometry(f'{width}x{height}+{x}+{y}')

def window_center2(win, width, height):
    # 获取屏幕宽度和高度
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    # 计算窗口位置
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    # 设置窗口大小和位置
    win.geometry(f'{width}x{height}+{x}+{y}')

# 自定义输入窗口
def custom_input_window(prompt, callback):
    input_window = Toplevel(root)  # 使用 Toplevel 而不是新的 Tk 实例
    input_window.title("输入")

    # 窗口居中显示相关
    input_window_width = 300
    input_window_height = 100
    window_center1(input_window, input_window_width, input_window_height)

    def on_ok():
        keyword = entry.get()
        input_window.destroy()
        callback(keyword)  # 回调函数处理关键词搜索

    def on_cancel():
        input_window.destroy()
        sys.exit(0)

    def on_esc(event):
        on_cancel()

    def on_enter(event):
        on_ok()  # 绑定回车键到 on_ok 函数

    Label(input_window, text=prompt).pack()
    entry = Entry(input_window)
    entry.pack()
    entry.focus_set()  # 激活输入框
    Button(input_window, text="确定", command=on_ok).pack(side="left")
    Button(input_window, text="取消", command=on_cancel).pack(side="right")

    entry.bind('<Return>', on_enter)  # 绑定回车键
    input_window.bind('<Escape>', on_esc)  # 绑定ESC键

# 搜索包含所有特定关键词的文件
def search_files(directories, keywords):
    matched_files = {}  # 使用字典来存储每个目录的匹配文件
    # 将关键字字符串拆分为列表，并转换为小写
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    for directory in directories:
        matched_files[directory] = []

        # 使用os.walk()遍历目录树
        for root, dirs, files in os.walk(directory):
            # 检查目录名是否以.workflow结尾
            for dir_name in dirs:
                if dir_name.endswith('.workflow'):
                    workflow_path = os.path.join(root, dir_name)
                    # 对于.workflow目录，特别处理
                    try:
                        wflow_path = os.path.join(workflow_path, 'contents/document.wflow')
                        with open(wflow_path, 'r') as file:
                            content = file.read().lower()  # 将内容转换为小写
                        # 确保内容包含所有关键词
                        if all(keyword_lower in content for keyword_lower in keywords_lower):
                            matched_files[directory].append(os.path.relpath(workflow_path, directory))
                    except Exception as e:
                        print(f"Error reading {wflow_path}: {e}")
            # 遍历文件
            for name in files:
                item_path = os.path.join(root, name)
                # 对.scpt文件特别处理
                if item_path.endswith('.scpt'):
                    try:
                        content = subprocess.check_output(['osadecompile', item_path], text=True).lower()  # 将内容转换为小写
                        # 确保内容包含所有关键词
                        if all(keyword_lower in content for keyword_lower in keywords_lower):
                            matched_files[directory].append(os.path.relpath(item_path, directory))
                    except Exception as e:
                        print(f"Error decompiling {item_path}: {e}")
                # 对.txt和.py文件直接读取内容
                elif item_path.endswith('.txt') or item_path.endswith('.py'):
                    try:
                        with open(item_path, 'r') as file:
                            content = file.read().lower()  # 将内容转换为小写
                        # 确保内容包含所有关键词
                        if all(keyword_lower in content for keyword_lower in keywords_lower):
                            matched_files[directory].append(os.path.relpath(item_path, directory))
                    except Exception as e:
                        print(f"Error reading {item_path}: {e}")

    return matched_files

# 自定义消息框展示结果
def show_results(results):
    # 新建窗口
    result_window = Toplevel(root)
    result_window.title("搜索结果")

    # 将窗口居中放置
    window_center2(result_window, 800, 600)  # 假设您想让窗口大小为 800x600
    
    # 创建滚动条
    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side="right", fill="y")
    
    # 创建文本框用于显示结果，设置宽度加倍
    text = Text(result_window, width=120, height=25, yscrollcommand=scrollbar.set)
    text.pack(side="left", fill="both")

    # 定义文本样式标签
    text.tag_configure('directory_tag', foreground='yellow', font=('Helvetica', '24', 'bold'))  # 用于目录的标签
    text.tag_configure('file_tag', foreground='orange', font=('Helvetica', '20'))  # 用于文件的标签
    
    # 将滚动条关联到文本框
    scrollbar.config(command=text.yview)

    # 清除文本框中的旧内容
    text.delete(1.0, "end")

    # 绑定 ESC 键到关闭窗口和结束程序的函数
    result_window.bind('<Escape>', lambda e: (result_window.destroy(), sys.exit(0)))
    
    # 插入文本到文本框
    if results:
        for directory, files in results.items():
            if files:
                text.insert("end", directory + "\n", 'directory_tag')
                text.insert("end", "\n".join(files) + "\n\n", 'file_tag')
    else:
        text.insert("end", "没有找到包含关键词的文件。")

# 等待用户输入关键词
custom_input_window("请输入要检索的字符串内容：", lambda keyword: show_results(search_files(searchFolders, keyword)))

root.mainloop()  # 最后，启动主事件循环