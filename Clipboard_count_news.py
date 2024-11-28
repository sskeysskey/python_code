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
    
    # 删除类似URL格式的字段，匹配 https://*.com、https://*.com/ 和 http://*.com 等格式
    url_pattern = r'https?://\S+\.com(?:/\S*)?'
    processed_content = re.sub(url_pattern, '', processed_content)
    
    # 将处理后的内容写回剪贴板
    pyperclip.copy(processed_content)
    
    return processed_content

def save_content_to_file(content, filepath):
    """将内容保存到指定文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"文件已创建：{filepath}")
    except IOError as e:
        print(f"创建文件时出错：{e}")

def count_words_and_create_file():
    # 处理剪贴板内容
    processed_content = process_clipboard_content()
    
    # 计算英文单词数量
    num_english_words = len(re.findall(r'\b[A-Za-z]+\b', processed_content))
    
    # 判断条件并创建相应文件
    if num_english_words > 2200:
        save_content_to_file(processed_content, '/tmp/longarticle.txt')
    elif num_english_words < 250:
        save_content_to_file(processed_content, '/tmp/shortarticle.txt')
    else:
        print(f"单词数量（{num_english_words}）在250-2200之间，不创建文件。")

if __name__ == '__main__':
    count_words_and_create_file()