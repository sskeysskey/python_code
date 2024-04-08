import os
import sys
import subprocess
from tkinter import Tk, filedialog, Text, Scrollbar, Button, Entry, Label, messagebox, Toplevel

# 初始化Tkinter，隐藏主窗口
root = Tk()
root.withdraw()

# 弹出选择文件夹对话框
searchFolder = filedialog.askdirectory(
    title="选择要检索的文件夹",
    mustexist=True
)
if not searchFolder:
    root.destroy()
    sys.exit(0)

def window_center(win, width, height):
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
    window_center(input_window, input_window_width, input_window_height)

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

# 搜索包含特定关键词的文件
def search_files(directory, keyword):
    matched_files = []
    # 将关键字转换为小写，以实现大小写不敏感的搜索
    keyword_lower = keyword.lower()

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
                    if keyword_lower in content:
                        matched_files.append(workflow_path)
                except Exception as e:
                    print(f"Error reading {wflow_path}: {e}")

        # 遍历文件
        for name in files:
            item_path = os.path.join(root, name)
            if item_path.endswith('.scpt'):
                # 对于.scpt文件，使用osascript命令来获取脚本内容
                try:
                    content = subprocess.check_output(['osadecompile', item_path], text=True).lower()  # 将内容转换为小写
                    if keyword_lower in content:
                        matched_files.append(item_path)
                except Exception as e:
                    print(f"Error decompiling {item_path}: {e}")
            elif item_path.endswith('.txt') or item_path.endswith('.py'):
                # 对于.txt文件和.py文件，直接读取内容
                try:
                    with open(item_path, 'r') as file:
                        content = file.read().lower()  # 将内容转换为小写
                    if keyword_lower in content:
                        matched_files.append(item_path)
                except Exception as e:
                    print(f"Error reading {item_path}: {e}")

    return matched_files

# 自定义消息框展示结果
def show_results(results):
    # 新建窗口
    result_window = Toplevel(root)
    result_window.title("搜索结果")

    # 将窗口居中放置
    window_center(result_window, 1000, 600)  # 假设您想让窗口大小为 800x600
    
    # 创建滚动条
    scrollbar = Scrollbar(result_window)
    scrollbar.pack(side="right", fill="y")
    
    # 创建文本框用于显示结果，设置宽度加倍
    text = Text(result_window, width=150, height=25, yscrollcommand=scrollbar.set)
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
        text.insert("end", "\n".join(results), 'file_tag')
    else:
        text.insert("end", "没有找到包含关键词的文件。")
    
# 在这里执行搜索并显示结果
def start_search(keyword):
    resultList = search_files(searchFolder, keyword)  # 执行搜索
    show_results(resultList)  # 显示结果

# 等待用户输入关键词
custom_input_window("请输入要检索的字符串内容：", start_search)

root.mainloop()  # 最后，启动主事件循环