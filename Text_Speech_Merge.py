import os
import subprocess
import sys
import tempfile

def merge_videos(video_files, output_file):
    # 在临时目录中创建一个文件列表
    with tempfile.NamedTemporaryFile(delete=False, mode='w', dir=tempfile.gettempdir(), suffix='.txt') as file_list:
        for video_file in video_files:
            file_list.write(f"file '{video_file}'\n")
        temp_file_list_path = file_list.name
    
    try:
        # 使用 FFmpeg 合并视频文件
        ffmpeg_path = "/opt/homebrew/bin/ffmpeg"  # 请将此路径替换为你系统中的实际路径
        command = [ffmpeg_path, "-f", "concat", "-safe", "0", "-i", temp_file_list_path, "-c", "copy", output_file]
        subprocess.run(command, check=True)
    finally:
        # 删除临时文件列表
        os.remove(temp_file_list_path)

def get_video_files(directory):
    # 获取指定目录下所有的MP4文件并按数字顺序排序
    video_files = sorted([os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4')],
                         key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    return video_files

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("请提供一个目录路径作为参数，例如：python merge_videos.py /path/to/directory")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"目录 {directory} 不存在或不是一个有效的目录。")
        sys.exit(1)
    
    video_files = get_video_files(directory)
    
    if not video_files:
        print(f"在目录 {directory} 下没有找到任何MP4文件。")
    else:
        output_file = os.path.join(directory, "output.mp4")
        merge_videos(video_files, output_file)
        print(f"视频已成功合并为 {output_file}")