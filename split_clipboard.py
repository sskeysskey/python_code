import pyperclip
import os

def find_nearest_sentence_end(text, start, end):
    # 在指定范围内查找最近的句号位置
    dot_positions = [text.rfind('.\n', start, end), text.rfind('。\n', start, end)]
    # 过滤掉找不到的情况
    valid_positions = [pos for pos in dot_positions if pos != -1]

    if valid_positions:
        # 返回最近的一个句号位置
        return max(valid_positions)
    else:
        # 如果没有句号，返回原分割点
        return end

def split_text(text, n):
    segments = []
    segment_length = len(text) // n
    start = 0

    for _ in range(n - 1):
        end = start + segment_length
        if end >= len(text):
            end = len(text) - 1

        nearest_end = find_nearest_sentence_end(text, start, end)
        segments.append(text[start:nearest_end + 1])
        start = nearest_end + 1

    if start < len(text):
        segments.append(text[start:])

    return segments

def save_segments(n, save_path="/Users/yanzhang/Downloads"):
    text = pyperclip.paste()
    segments = split_text(text, n)

    for i, segment in enumerate(segments):
        if segment:
            file_path = os.path.join(save_path, f'segment_{i + 1}.txt')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(segment)
            print(f"第{i + 1}部分已保存到: {file_path}")
