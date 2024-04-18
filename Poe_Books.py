import re
import os
import glob
import pyperclip

def rename_first_segment_file(directory):
    # 构造搜索路径
    search_pattern = os.path.join(directory, 'segment_*.txt')
    
    # 使用glob找到所有符合条件的文件
    files = glob.glob(search_pattern)
    
    # 定义一个函数用于从文件名中提取数字，并确保正确处理文件名数字
    def extract_number(filename):
        # 从完整路径中提取文件名部分
        basename = os.path.basename(filename)
        # 使用正则表达式匹配数字
        match = re.search(r'segment_(\d+)\.txt', basename)
        return int(match.group(1)) if match else float('inf')
    
    # 检查是否找到了文件
    if files:
        # 按文件名中数字排序
        files.sort(key=extract_number)
        # 获取数值最小的文件（列表中的第一个文件）
        min_file = files[0]
        # 构造新文件名
        new_name = re.sub(r'segment_(\d+)\.txt', r'done_\1.txt', min_file)
        # 改名操作
        os.rename(min_file, new_name)
        print(f"已将文件 {min_file} 改名为 {new_name}")
    else:
        print("没有找到以 'segment_' 开头的txt文件")

# 主函数
def main():
    # 设置目录路径
    directory_path = '/Users/yanzhang/Documents/'

    # 寻找目录下的第一个txt文件
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            txt_file_path = os.path.join(directory_path, filename)
            break  # 找到第一个txt文件后停止循环

    # 读取剪贴板内容
    clipboard_content = pyperclip.paste()

    # 检查clipboard_content是否为None或者是否是一个字符串
    if clipboard_content:
        # 计算剪贴板内容中的中文字符数目
        chinese_characters_count = len(re.findall(r'[\u4e00-\u9fff]+', clipboard_content))

        # 检查是否同时包含"色情"和"露骨"关键字
        if "露骨" in clipboard_content and chinese_characters_count < 250:
            print("剪贴板内容不符合要求，程序终止执行。")
            # 内容非法后的过渡传递参数
            pyperclip.copy("illegal")
            exit()

        # 使用splitlines()分割剪贴板内容为多行
        lines = clipboard_content.splitlines()
        # 移除空行
        non_empty_lines = [line for line in lines if line.strip()]
    else:
        print("剪贴板中没有内容或pyperclip无法访问剪贴板。")
        non_empty_lines = []  # 确保non_empty_lines是一个列表，即使剪贴板为空

    # 将非空行合并为一个字符串，用换行符分隔
    modified_content = '\n'.join(non_empty_lines)

    # 读取/tmp/segment.txt文件内容
    segment_file_path = '/tmp/segment.txt'
    with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
        segment_content = segment_file.read().strip()  # 使用strip()移除可能的空白字符

    # 在segment_content后面添加一个换行符
    segment_content += '\n'
    
    # 将读取到的segment_content内容插入在剪贴板内容的最前面
    final_content = segment_content + modified_content

    # 追加处理后的内容到TXT文件
    with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
        txt_file.write(final_content)
        txt_file.write('\n\n')  # 添加两个换行符以创建一个空行

    # 使用函数
    directory = "/Users/yanzhang/Downloads/backup/TXT/Segments/"
    rename_first_segment_file(directory)

    # 删除/tmp/segment.txt文件
    os.remove(segment_file_path)

if __name__ == '__main__':
    main()