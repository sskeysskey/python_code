import re
import pyautogui
import pyperclip
from time import sleep

pyautogui.moveTo(485, 662)
sleep(0.5)
pyautogui.click(button='right')
sleep(0.5)
# 移动鼠标并再次点击
pyautogui.moveRel(110, 118)  # 往左移动110，往下移动118
sleep(0.5)
pyautogui.click()  # 执行点击操作
sleep(1)

# 设置TXT文件的保存路径
txt_file_path = '/Users/yanzhang/Documents/book.txt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 使用splitlines()分割剪贴板内容为多行
lines = clipboard_content.splitlines()
# 移除空行
non_empty_lines = [line for line in lines if line.strip()]

# 判断是否只有一行内容
if len(non_empty_lines) == 1:
    modified_content = clipboard_content
else:
    # 判断第一句是否以“首先”或“第一”开头
    first_sentence_start_with_special = non_empty_lines and \
        (non_empty_lines[0].startswith('首先') or non_empty_lines[0].startswith('第一'))

    # 计算非空行中以数字或符号开头的行数
    num_start_with_digit_symbol_or_chinese_char = sum(bool(re.match(r'^[\d\W]|^第', line)) for line in non_empty_lines)

    # 判断是否超过50%
    if num_start_with_digit_symbol_or_chinese_char > len(non_empty_lines) / 2:
        # 判断最后一行是否以数字或“第”字开头
        if not non_empty_lines[-1].startswith(('第',)) and not re.match(r'^\d', non_empty_lines[-1]):
            # 如果不是，则剪贴板中第一行和最后一句都删除
            modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):-1])
        else:
            # 如果是，则只删除第一行
            modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])
    else:
        # 如果不足50%，则只删除第一句（除非第一句以“首先”或“第一”开头）
        modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])

# 读取/tmp/segment.txt文件内容
segment_file_path = '/tmp/segment.txt'
with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
    segment_content = segment_file.read()

# 在segment_content后面添加一个换行符
segment_content += '\n'

# 将读取到的segment_content内容插入在剪贴板内容的最前面
final_content = segment_content + modified_content

# 追加处理后的内容到TXT文件
with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
    txt_file.write(final_content)
    txt_file.write('\n\n')  # 添加两个换行符以创建一个空行