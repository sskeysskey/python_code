import os
from datetime import datetime

# 设置stop_signal文件的保存目录
stop_signal_directory = '/private/tmp'

# 设置stop_signal文件的保存路径
now = datetime.now()
time_str = now.strftime("_%m_%d_%H")
stop_signal_file_name = f"stop_signal{time_str}.txt"
stop_signal_path = os.path.join(stop_signal_directory, stop_signal_file_name)

with open(stop_signal_path, 'w') as signal_file:
        signal_file.write('stop')