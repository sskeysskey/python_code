import re
import os
import time
import codecs
import pyautogui
import pyperclip
import webbrowser
import subprocess
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from html.parser import HTMLParser

# 从剪贴板读取翻译后的内容
def get_clipboard_data():
    p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
    data, _ = p.communicate()
    return data.decode('utf-8').splitlines()

# 将修改后的内容写回剪贴板
def set_clipboard_data(data):
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.stdin.write(data.encode('utf-8'))
    p.stdin.close()
    p.wait()

# 解析HTML并替换链接文本
class MyHTMLParser(HTMLParser):
    def __init__(self, new_texts):
        super().__init__()
        self.new_texts = new_texts
        self.current_index = 0
        self.result_html = ""
        self.inside_a = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.inside_a = True
            for attr in attrs:
                if attr[0] == "target" and attr[1] == "_blank":
                    self.capture = True
        self.result_html += self.get_starttag_text()

    def handle_endtag(self, tag):
        if tag == "a":
            self.inside_a = False
            self.current_index += 1
        self.result_html += f"</{tag}>"

    def handle_data(self, data):
        if self.inside_a and getattr(self, 'capture', False):
            if self.current_index < len(self.new_texts):
                self.result_html += self.new_texts[self.current_index]
            else:
                # 如果新文本行数不够，则抛出错误
                raise IndexError("剪贴板内容行数与原文链接数量不匹配。")
        else:
            self.result_html += data

# 文件路径
file_path = "/Users/yanzhang/Documents/News/today_chn.txt"
# 获取剪贴板内容
clipboard_content = pyperclip.paste()

# 检查文件是否存在，不存在则创建
if not os.path.exists(file_path):
    # 使用'w'模式创建文件，如果文件已经存在，'w'模式会覆盖文件，所以前面要检查文件是否存在
    with codecs.open(file_path, 'w', 'utf-8') as file:
        file.write(clipboard_content + '\n')  # 写入剪贴板内容并在最后加入换行符
else:
    # 如果文件存在，则追加内容
    with codecs.open(file_path, 'a', 'utf-8') as file:
        file.write(clipboard_content + '\n')  # 追加剪贴板内容并在最后加入换行符

# 读取文件内容，并去除空行
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
    non_empty_lines = [line for line in lines if line.strip()]

# 合并非空行，并去除尾部的换行符
content_to_copy = ''.join(non_empty_lines).rstrip('\n')

# 将内容复制到剪贴板
pyperclip.copy(content_to_copy)

# 读取剪贴板中翻译后的内容
translated_texts = get_clipboard_data()

# 过滤掉空行
translated_texts = [line for line in translated_texts if line.strip() != '']

# 读取HTML文件内容
with open('/Users/yanzhang/Documents/News/today_eng.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# 创建解析器实例并传入翻译后的内容
parser = MyHTMLParser(translated_texts)

try:
    # 解析并替换文本
    parser.feed(html_content)

    # 如果新文本数量与原始链接数量相同，则写回文件
    if parser.current_index == len(translated_texts):
        # 定义原始和目标文件路径
        original_file_path = '/Users/yanzhang/Documents/News/today_eng.html'
        
        with open(original_file_path, 'w', encoding='utf-8') as file:
            file.write(parser.result_html)
        print("文件已成功更新。")
        os.remove(file_path)

        # 设置TXT文件的保存路径
        now = datetime.now()
        time_str = now.strftime("_%m_%d")
        txt_file_name = f"TodayCNH{time_str}.html"
        txt_directory = '/Users/yanzhang/Documents/News'
        txt_file_path = os.path.join(txt_directory, txt_file_name)

        # 重命名文件
        os.rename(original_file_path, txt_file_path)
        print(f"文件已重命名为：{txt_file_path}")
    else:
        clip_content = pyperclip.paste()
        if clip_content == "stop":
            raise IndexError("翻译完的内容行数与原英文链接的数量不匹配，请检查。")
        else:
            script_path = '/Users/yanzhang/Documents/ScriptEditor/Trans_News_Title.scpt'
            try:
                # 执行指定路径的AppleScript
                process = subprocess.run(['osascript', script_path], check=True, text=True, stdout=subprocess.PIPE)
                # 输出AppleScript的返回结果
                print(process.stdout.strip())
            except subprocess.CalledProcessError as e:
                # 如果有错误发生，打印错误信息
                print(f"执行AppleScript时出错: {e}")
        
except IndexError as e:
    # 初始化Tkinter窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showerror("错误", str(e))  # 弹出错误对话框
    root.destroy()  # 销毁窗口

# 检查文件是否存在
if os.path.exists(txt_file_path):
    # 如果文件存在，使用webbrowser打开它
    webbrowser.open('file://' + os.path.realpath(txt_file_path), new=2)
    time.sleep(0.5)
    # 循环7次模拟按下Command + '='快捷键
    for _ in range(7):
        pyautogui.hotkey('command', '=')
        time.sleep(0.2)  # 在连续按键之间添加小延迟，以模拟自然按键速度
else:
    print("文件不存在，无法打开。")