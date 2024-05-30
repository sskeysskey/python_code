import subprocess
import pyperclip
import time
import tkinter as tk
from tkinter import messagebox

# 初始化 Tkinter 主窗口
root = tk.Tk()
root.withdraw()  # 这行代码可以隐藏主窗口，只显示弹出的消息框

originalClipboard = pyperclip.paste()
messagebox.showerror("剪贴板内容", f"original是{originalClipboard}")

script_path = '/Users/yanzhang/Documents/ScriptEditor/Copy_Clipboard.scpt'
try:
    # 将坐标值作为参数传递给AppleScript
    process = subprocess.run(['osascript', script_path], check=True, text=True, stdout=subprocess.PIPE)
    # 输出AppleScript的返回结果
    print(process.stdout.strip())
except subprocess.CalledProcessError as e:
    # 如果有错误发生，打印错误信息
    print(f"Error running AppleScript: {e}")

newClipboard = pyperclip.paste()

# 使用 messagebox 显示新的剪贴板内容
messagebox.showerror("剪贴板内容", f"newclipboard是{newClipboard}")

# 运行 Tkinter 事件循环，直到所有窗口都关闭
root.mainloop()