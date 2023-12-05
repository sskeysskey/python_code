# clipboard_split.py

import pyperclip
import os

def split_text(text, n):
    # 分割文本为n份
    segments = []
    segment_length = len(text) // n
    start = 0
    for _ in range(n - 1):
        end = text.find(".\n", start + segment_length)
        if end == -1:  # 如果找不到".\n"，则直接到文本末尾
            end = len(text)
        segments.append(text[start:end + 2])  # 包含".\n"
        start = end + 2
    segments.append(text[start:])  # 添加最后一段
    return segments

def save_segments(n, save_path="/Users/yanzhang/Downloads"):
    # 从剪贴板读取文本
    text = pyperclip.paste()

    # 分割文本
    segments = split_text(text, n)

    # 直接保存到指定路径
    for i, segment in enumerate(segments):
        file_path = os.path.join(save_path, f'segment_{i + 1}.txt')
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(segment)
        print(f"第{i + 1}部分已保存到: {file_path}")
