import re
import pyperclip
import os

def count_words_and_create_file():
    # 获取剪贴板内容
    clipboard_content = pyperclip.paste()
    
    # 计算英文单词数量
    num_english_words = len(re.findall(r'\b[A-Za-z]+\b', clipboard_content))
    
    # 判断是否超过2000个单词
    if num_english_words > 2000:
        file_path = '/tmp/longarticle.txt'
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clipboard_content)
            print(f"文件已创建：{file_path}")
        except IOError as e:
            print(f"创建文件时出错：{e}")
    else:
        print(f"单词数量（{num_english_words}）不超过2000，不创建文件。")

if __name__ == '__main__':
    count_words_and_create_file()