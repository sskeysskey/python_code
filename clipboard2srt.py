import pyperclip
import os
from datetime import datetime

# 设置SRT文件的保存目录
srt_directory = '/Users/yanzhang/Movies'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 首先检查剪贴板内容的第一位字符是否是数字1
if clipboard_content and clipboard_content[0] == '1':
    # 是数字1，根据当前时间创建新文件
    now = datetime.now()
    time_str = now.strftime("_%m_%d_%H_%M")
    srt_file_path = os.path.join(srt_directory, f"subtitles{time_str}.srt")
else:
    # 不是数字1，找到时间最新的文件进行追加
    srt_files = [f for f in os.listdir(srt_directory) if f.startswith('subtitles') and f.endswith('.srt')]
    latest_file = None
    if len(srt_files) == 1:
        # 只有一个文件，直接使用该文件
        latest_file = srt_files[0]
    elif len(srt_files) >= 2:
        # 有两个或更多文件，需要比较时间戳找出最新的文件
        latest_time = datetime.min
        for srt_file in srt_files:
            # 解析文件名中的时间
            time_part = srt_file.replace('subtitles_', '').replace('.srt', '')
            try:
                file_time = datetime.strptime(time_part, "%m_%d_%H_%M")
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = srt_file
            except ValueError:
                # 如果文件名不包含有效的时间格式，则忽略该文件
                pass
    # 如果没有找到符合条件的文件，则创建新文件名
    if not latest_file:
        now = datetime.now()
        time_str = now.strftime("_%m_%d_%H_%M")
        latest_file = f"subtitles{time_str}.srt"
    # 完整的SRT文件路径
    srt_file_path = os.path.join(srt_directory, latest_file)

# 追加剪贴板内容到SRT文件，并在最后添加一个空行
with open(srt_file_path, 'a', encoding='utf-8-sig') as f:
    f.write(clipboard_content)
    f.write('\n\n')  # 添加两个换行符以创建一个空行