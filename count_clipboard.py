import pyperclip
import re
import os

# 获取剪贴板内容
clipboard_content = pyperclip.paste()

# 计算剪贴板内容的总字符数量
total_characters = len(clipboard_content)

# 计算中文字符的数量
num_chinese_characters = len(re.findall(r'[\u4e00-\u9fff]', clipboard_content))

# 计算英文单词的数量
num_english_words = len(re.findall(r'\b[A-Za-z]+\b', clipboard_content))

# 计算不是英文字母（a-z，A-Z）、数字（0-9）或空格的字符数量
num_symbols = sum(not ch.isalnum() and not ch.isspace() for ch in clipboard_content)

# 弹窗显示结果
os.system(f"osascript -e 'display alert \"剪贴板分析\" message \"总共字符： {total_characters} \n中文字符： {num_chinese_characters} \n英文单词： {num_english_words} \n符号数量： {num_symbols} \"'")