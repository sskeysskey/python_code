import codecs
import pyperclip
import re

def process_clipboard_content(clipboard_content):
    """处理剪贴板内容，取消两行之间只有一个换行符的情况，并在合并的句子之间增加一个空格。"""
    # 统计空行数量
    empty_lines = len(re.findall(r'\n\s*\n', clipboard_content))
    
    # 如果有不止一个空行，进行单行换行符的合并并在合并的句子之间增加一个空格
    if empty_lines > 0:
        processed_content = re.sub(r'(?<!\n)\n(?!\n)', ' ', clipboard_content)
    else:
        processed_content = clipboard_content
    
    return processed_content

def SRT_File(clipboard_content):
    """处理剪贴板内容并写入文件。"""
    print("已写入bob.txt")
    # 定义文件路径
    file_path = '/Users/yanzhang/Downloads/bob.txt'

    # 检查文件是否存在，不存在则创建
    with codecs.open(file_path, 'a', 'utf-8') as file:
        file.write(clipboard_content + '\n')  # 追加剪贴板内容并在最后加入换行符

# 主函数
def main():
    try:
        # 获取剪贴板内容
        clipboard_content = pyperclip.paste()
        processed_content = process_clipboard_content(clipboard_content)
        SRT_File(processed_content)
    except pyperclip.PyperclipException as e:
        print("无法访问剪贴板，请检查pyperclip是否支持当前系统。")

if __name__ == '__main__':
    main()