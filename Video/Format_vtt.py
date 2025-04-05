import re

def process_vtt_file(input_file, output_file):
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 把文件按照空行分隔为字幕块
    blocks = content.split('\n\n')
    processed_blocks = []
    
    # 跳过WEBVTT块（不保留）
    if blocks and blocks[0].strip().startswith('WEBVTT'):
        blocks = blocks[1:]  # 跳过WEBVTT块
    
    i = 0
    while i < len(blocks):
        block = blocks[i].strip()
        lines = block.split('\n')
        
        # 检查是否为有效的字幕块（至少包含时间行和文本行）
        timestamp_pattern = r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$'
        
        # 情况1: 如果块不包含时间戳行，则跳过
        if not any(re.match(timestamp_pattern, line) for line in lines):
            i += 1
            continue
        
        # 情况2: 如果时间戳行后面有空行，再跟文本行，则跳过整个块
        has_empty_line = False
        for j in range(len(lines)):
            if re.match(timestamp_pattern, lines[j]):
                if j + 1 < len(lines) and lines[j + 1].strip() == '':
                    has_empty_line = True
                    break
        
        if has_empty_line:
            i += 1
            continue
        
        # 情况3: 如果时间戳行后面没有文本行，跳过该块
        has_text = False
        for j in range(len(lines)):
            if re.match(timestamp_pattern, lines[j]):
                if j + 1 < len(lines) and lines[j + 1].strip() != '':
                    has_text = True
                    break
        
        if not has_text:
            i += 1
            continue
            
        # 保存当前有效块以备后续检查重复文本
        processed_blocks.append(block)
        i += 1
    
    # 处理连续多行内容相同的情况（合并）
    final_blocks = []
    i = 0
    
    while i < len(processed_blocks):
        current_block = processed_blocks[i]
        current_lines = current_block.strip().split('\n')
        
        # 提取时间戳和文本
        timestamp_pattern = r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$'
        if len(current_lines) >= 2:
            # 找到时间戳行的索引
            timestamp_idx = -1
            for j, line in enumerate(current_lines):
                if re.match(timestamp_pattern, line):
                    timestamp_idx = j
                    break
                    
            if timestamp_idx != -1:
                timestamp_line = current_lines[timestamp_idx]
                start_time = timestamp_line.split(' --> ')[0]
                # 获取时间戳后的所有文本行
                text_content = '\n'.join(current_lines[timestamp_idx+1:])
                
                # 查找连续的相同内容块
                j = i + 1
                while j < len(processed_blocks):
                    next_block = processed_blocks[j]
                    next_lines = next_block.strip().split('\n')
                    
                    # 找到下一个块的时间戳行
                    next_timestamp_idx = -1
                    for k, line in enumerate(next_lines):
                        if re.match(timestamp_pattern, line):
                            next_timestamp_idx = k
                            break
                            
                    if next_timestamp_idx != -1:
                        next_text = '\n'.join(next_lines[next_timestamp_idx+1:])
                        
                        # 如果文本内容相同，合并时间戳
                        if next_text == text_content:
                            end_time = next_lines[next_timestamp_idx].split(' --> ')[1]
                            j += 1
                        else:
                            break
                    else:
                        break
                
                if j > i + 1:  # 有需要合并的块
                    end_time = None
                    for k in range(j-1, i, -1):
                        next_lines = processed_blocks[k].strip().split('\n')
                        for line in next_lines:
                            if re.match(timestamp_pattern, line):
                                end_time = line.split(' --> ')[1]
                                break
                        if end_time:
                            break
                    
                    if end_time:
                        merged_block = f"{start_time} --> {end_time}\n{text_content}"
                        final_blocks.append(merged_block)
                    else:
                        final_blocks.append(current_block)
                    i = j
                else:
                    final_blocks.append(current_block)
                    i += 1
            else:
                final_blocks.append(current_block)
                i += 1
        else:
            final_blocks.append(current_block)
            i += 1
    
    # 添加编号
    numbered_blocks = []
    counter = 1
    
    for block in final_blocks:
        lines = block.strip().split('\n')
        numbered_block = f"{counter}\n{block}"
        numbered_blocks.append(numbered_block)
        counter += 1
    
    # 写入处理后的内容到输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(numbered_blocks))

# 用法示例
input_file = '/Users/yanzhang/Downloads/backup/local_video/output/transcript.vtt'
output_file = '/Users/yanzhang/Downloads/transcript.srt'
process_vtt_file(input_file, output_file)