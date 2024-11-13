import pyperclip

def process_content_with_empty_lines(text):
    """
    处理含有多个空行的文本内容
    - 如果有超过5个空行，进行特殊处理
    - 合并没有空行分隔的句子
    - 保持有空行分隔的句子之间只有一个换行符
    """
    # 将文本分割成行
    lines = text.splitlines()
    
    # 计算空行数量
    empty_line_count = sum(1 for line in lines if not line.strip())
    
    # 如果空行少于5个，直接返回原始文本
    if empty_line_count <= 5:
        return text
    
    # 处理多空行情况
    result = []
    current_segment = []
    
    for line in lines:
        if line.strip():  # 非空行
            current_segment.append(line)
        else:  # 空行
            if current_segment:  # 如果当前段落有内容
                # 将当前段落合并为一行
                result.append(' '.join(current_segment))
                current_segment = []
            if result and not result[-1] == '':  # 确保只添加一个空行
                result.append('')
    
    # 处理最后一个段落
    if current_segment:
        result.append(' '.join(current_segment))
    
    return '\n'.join(result)

# 从剪贴板读取内容
clipboard_content = pyperclip.paste()
# 处理内容
clipboard_content1 = process_content_with_empty_lines(clipboard_content)
# 将处理后的内容写回剪贴板
pyperclip.copy(clipboard_content1)