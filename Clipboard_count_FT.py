import re
import pyperclip
import os

def process_clipboard_content():
    # 获取剪贴板内容
    clipboard_content = pyperclip.paste()
    
    # 查找只包含"Close"的行，并删除该行及其之前的所有内容
    pattern = r'^.*\n.*?\bClose\b\s*$'
    match = re.search(pattern, clipboard_content, re.MULTILINE | re.DOTALL)
    
    if match:
        processed_content = clipboard_content[match.end():].strip()
    else:
        processed_content = clipboard_content
    
    # 将处理后的内容写回剪贴板
    pyperclip.copy(processed_content)
    
    return processed_content

def count_words_and_create_file():
    # 处理剪贴板内容
    processed_content = process_clipboard_content()
    
    # 计算英文单词数量
    num_english_words = len(re.findall(r'\b[A-Za-z]+\b', processed_content))
    
    # 判断是否超过2000个单词
    if num_english_words > 2000:
        file_path = '/tmp/longarticle.txt'
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            print(f"文件已创建：{file_path}")
        except IOError as e:
            print(f"创建文件时出错：{e}")
    else:
        print(f"单词数量（{num_english_words}）不超过2000，不创建文件。")

if __name__ == '__main__':
    count_words_and_create_file()