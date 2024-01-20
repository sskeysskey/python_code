import pyperclip
import re

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 使用splitlines()分割剪贴板内容为多行
lines = clipboard_content.splitlines()
# 移除空行
non_empty_lines = [line for line in lines if line.strip()]

# 判断第一句是否以“首先”或“第一”开头
first_sentence_start_with_special = non_empty_lines and \
    (non_empty_lines[0].startswith('首先') or non_empty_lines[0].startswith('第一'))

# 计算非空行中以数字或符号开头的行数
num_start_with_digit_symbol_or_chinese_char = sum(
    bool(re.match(r'^[\d\W]|^第', line)) for line in non_empty_lines
)

# 判断是否超过50%
if num_start_with_digit_symbol_or_chinese_char >= len(non_empty_lines) / 2:
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

# 将处理后的内容复制回剪贴板
pyperclip.copy(modified_content)