import os
import sys
import codecs
import pyperclip
sys.path.append('/Users/yanzhang/Documents/python_code/Modules')
from Rename_segment import rename_first_segment_file

def remove_empty_lines(text):
    """移除文本中的空行."""
    return '\n'.join([line for line in text.splitlines() if line.strip()])

def NewsTitle_File(clipboard_content):
    """处理剪贴板内容并写入文件."""
    print("执行函数B")
    # 定义文件路径
    file_path = '/Users/yanzhang/Documents/News/today_chn.txt'
    
    # 移除剪贴板内容中的空行
    clipboard_content = remove_empty_lines(clipboard_content)

    # 检查文件是否存在，不存在则创建
    with codecs.open(file_path, 'a', 'utf-8') as file:
        file.write(clipboard_content + '\n')  # 追加剪贴板内容并在最后加入换行符

# 主函数
def main():
    try:
        # 获取剪贴板内容
        clipboard_content = pyperclip.paste()
        NewsTitle_File(clipboard_content)
    except pyperclip.PyperclipException as e:
        print("无法访问剪贴板，请检查pyperclip是否支持当前系统。")

if __name__ == '__main__':
    main()
    # 使用函数
    directory = "/tmp/"
    rename_first_segment_file(directory)