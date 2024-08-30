import os
import glob
import codecs
import re
import sys
import pyperclip
sys.path.append('/Users/yanzhang/Documents/python_code/Modules')
from Rename_segment import rename_first_segment_file

def count_non_empty_lines(content):
    return sum(1 for line in content.splitlines() if line.strip())

def extract_number(filename):
    basename = os.path.basename(filename)
    match = re.search(r'segment_(\d+)\.txt', basename)
    return int(match.group(1)) if match else None

def find_min_segment_file(directory):
    search_pattern = os.path.join(directory, 'segment_*.txt')
    files = glob.glob(search_pattern)
    valid_files = [f for f in files if extract_number(f) is not None]
    return min(valid_files, key=extract_number) if valid_files else None

def NewsTitle_File(clipboard_content, file_path):
    """处理剪贴板内容并写入文件."""
    print("执行函数 NewsTitle_File")
    
    # 移除剪贴板内容中的空行
    clipboard_content = remove_empty_lines(clipboard_content)
    
    # 如果文件为空，直接写入内容并添加换行符。如果文件不为空且最后一个字符不是换行符，添加一个换行符后再写入新内容，否则直接写入新内容。
    if clipboard_content:
        with codecs.open(file_path, 'a+', 'utf-8') as file:
            file.seek(0, os.SEEK_END)
            if file.tell() > 0:
                file.seek(file.tell() - 1, os.SEEK_SET)
                if file.read(1) != '\n':
                    file.write('\n')
            file.write(clipboard_content + '\n')
    else:
        print("剪贴板内容为空，未写入文件。")

def remove_empty_lines(text):
    """移除文本中的空行."""
    return '\n'.join(line for line in text.splitlines() if line.strip())

def main():
    directory = "/tmp/"
    file_path = '/Users/yanzhang/Documents/News/today_chn.txt'
    
    try:
        # 获取剪贴板内容并计算非空行数
        clipboard_content = pyperclip.paste()
        clipboard_lines = count_non_empty_lines(clipboard_content)
        
        if clipboard_lines == 0:
            print("剪贴板为空或内容无效。")
            return
        
        # 查找最小数字的 segment 文件
        min_file = find_min_segment_file(directory)
        
        if min_file:
            # 读取文件内容并计算非空行数
            with open(min_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            file_lines = count_non_empty_lines(file_content)
            
            # 比较行数
            if clipboard_lines != file_lines:
                # 如果不同，创建 diff.txt
                diff_file = os.path.join(directory, 'diff.txt')
                with open(diff_file, 'w', encoding='utf-8') as diff:
                    diff.write(f"剪贴板行数: {clipboard_lines}\n文件行数: {file_lines}\n")
                print(f"行数不同。已创建 {diff_file}")
            else:
                NewsTitle_File(clipboard_content, file_path)
                rename_first_segment_file(directory)
                print("行数相同。程序执行完毕。")
        else:
            print("未找到符合条件的 segment 文件。")
    
    except Exception as e:
        print(f"程序出错: {e}")

if __name__ == "__main__":
    main()