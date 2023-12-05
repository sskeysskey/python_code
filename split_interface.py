import tkinter as tk
from tkinter.font import Font
from split_clipboard import save_segments

def on_escape(event=None):
    root.destroy()

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 3) - (height // 2)
    win.geometry(f'{width}x{height}+{x}+{y}')

def on_split(event=None):
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
        root.destroy()  # 执行完毕后关闭窗口
    except Exception as e:
        info_label.config(text=f"发生错误：{e}")

# 创建 Tkinter 窗口
root = tk.Tk()
root.title("分割文本")

# 设置字体
font = Font(family="Helvetica", size=24)

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

# 创建按钮
#split_button = tk.Button(root, text="分割", command=on_split, font=font)
#split_button.pack(pady=10, padx=60)

# 窗口居中
center_window(root)

# 运行 Tkinter 事件循环
root.mainloop()
