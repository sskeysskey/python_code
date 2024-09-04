import os
import tkinter as tk
from tkinter import filedialog, messagebox

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title='选择要处理的文件',
        filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
    )
    root.destroy()
    return file_path

def process_file(file_path):
    file_name = os.path.basename(file_path)
    cleaned_name = os.path.splitext(file_name.replace(' ', ''))[0]
    
    mp3name_path = "/tmp/mp3name.txt"
    with open(mp3name_path, 'w', encoding='utf-8') as mp3name_file:
        mp3name_file.write(cleaned_name)
    print(f"文件名已保存到: {mp3name_path}")

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    max_length = 2600
    parts = []
    current_part = ""
    current_length = 0

    for char in content:
        current_part += char
        current_length += 1
        
        if char in '。!?！？':
            if current_length > max_length:
                parts.append(current_part)
                current_part = ""
                current_length = 0
        elif current_length >= max_length:
            last_sentence_end = max(current_part.rfind('。'), 
                                    current_part.rfind('!'), 
                                    current_part.rfind('?'),
                                    current_part.rfind('！'), 
                                    current_part.rfind('？'))
            if last_sentence_end != -1:
                parts.append(current_part[:last_sentence_end+1])
                current_part = current_part[last_sentence_end+1:]
                current_length = len(current_part)
            else:
                parts.append(current_part)
                current_part = ""
                current_length = 0

    if current_part:
        parts.append(current_part)

    for i, part in enumerate(parts, 1):
        part_file_path = f"/tmp/textspeech_{i}.txt"
        with open(part_file_path, 'w', encoding='utf-8') as part_file:
            part_file.write(part)
        print(f"生成文件: {part_file_path}")

    print("文件切割完成。")

def main():
    try:
        file_path = select_file()
        if not file_path:
            print('没有选择文件。')
            return

        process_file(file_path)
    except Exception as e:
        messagebox.showerror("错误", f"处理过程中发生错误：{str(e)}")
        print(f"发生错误：{str(e)}")

if __name__ == "__main__":
    main()