import re
import os
import datetime
import pyperclip

def SRT_File(clipboard_content):
    print("执行函数A")
    # 使用正则表达式找到第一个以数字开头并且紧跟一个换行符的行
    match = re.search(r'^(\d+).*\n', clipboard_content, re.MULTILINE)

    # 获取当前日期并格式化为指定的文件名形式
    current_date = datetime.datetime.now().strftime('%m月%d日%H%M.srt')

    # 拼接文件完整路径
    file_path = os.path.join('/Users/yanzhang/Movies', current_date)

    if match:
        start_index = match.start()  # 获取匹配行的起始索引
        number_at_start = int(match.group(1))  # 获取行首的数字
        remaining_content = clipboard_content[start_index:]  # 截取剩余内容

        # 根据行首数字决定是创建新文件还是追加现有文件
        if number_at_start == 1 or not os.path.exists(file_path):
            mode = 'w'  # 创建新文件
        else:
            mode = 'a'  # 追加到现有文件

        # 写入文件
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(remaining_content)
            file.write('\n\n')  # 添加两个换行符以创建一个空行
        print('内容处理完成，已经写入到', file_path)
    else:
        print('剪贴板内容中没有找到符合条件的行。')

# 主函数
def main():
    try:
        # 获取剪贴板内容
        clipboard_content = pyperclip.paste()
        SRT_File(clipboard_content)
    except pyperclip.PyperclipException as e:
        print("无法访问剪贴板，请检查pyperclip是否支持当前系统。")

if __name__ == '__main__':
    main()