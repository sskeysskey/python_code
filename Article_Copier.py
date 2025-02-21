import cv2
import numpy as np
from PIL import ImageGrab
import os
import sys
from datetime import datetime
import time
import shutil
import glob

def capture_screen():
    """
    使用PIL的ImageGrab直接截取屏幕，并转换为OpenCV格式
    """
    screenshot = ImageGrab.grab()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def find_image_on_screen(template, threshold=0.9):
    """
    在当前屏幕中查找给定模板图像的匹配位置（精度默认0.9）。
    如果找到，则返回 (top_left坐标, 模板形状)，否则返回 (None, None)。
    """
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    # 释放截图及相关资源
    del screen
    if max_val >= threshold:
        return max_loc, template.shape
    return None, None

def write_to_failure_file(url):
    """
    将URL写入失败记录文件
    """
    file_path = "/Users/yanzhang/Documents/News/Copier_failure.txt"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"[{current_time}] {url}\n"
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)

def move_and_record_images(url):
    """
    移动jpg图片并记录到article_copier.txt
    """
    source_dir = "/Users/yanzhang/Downloads"
    target_dir = "/Users/yanzhang/Downloads/news_image"
    record_file = "/Users/yanzhang/Documents/News/article_copier.txt"

    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(os.path.dirname(record_file), exist_ok=True)

    # 获取所有jpg文件
    jpg_files = glob.glob(os.path.join(source_dir, "*.jpg"))
    moved_files = []

    # 移动文件
    for jpg_file in jpg_files:
        filename = os.path.basename(jpg_file)
        target_path = os.path.join(target_dir, filename)
        shutil.move(jpg_file, target_path)
        moved_files.append(filename)

    # 写入记录文件
    if moved_files:
        content = f"{url}\n\n" + "\n".join(moved_files) + "\n\n"
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(content)

def main():
    # 获取传入的URL参数
    url = sys.argv[1] if len(sys.argv) > 1 else "No URL provided"
    
    # 定义模板路径字典
    template_paths = {
        "failure": "/Users/yanzhang/Documents/python_code/Resource/copier_text_failure.png",
        "success1": "/Users/yanzhang/Documents/python_code/Resource/copier_image_success1.png",
        "success2": "/Users/yanzhang/Documents/python_code/Resource/copier_image_success2.png"
    }

    # 读取所有模板图片
    templates = {}
    for key, path in template_paths.items():
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {path}")
        templates[key] = template

    # 先检查failure图片
    location_failure, shape_failure = find_image_on_screen(templates["failure"])
    
    if location_failure:
        print(f"找到failure图片位置: {location_failure}")
        write_to_failure_file(url)
    # else:
    #     # 如果没找到failure图片，给5秒时间找success图片
    #     print("未找到failure图片，开始寻找success图片...")
    #     start_time = time.time()
    #     success_found = False
        
    #     while time.time() - start_time < 5:  # 5秒时间限制
    #         # 同时检查两个success图片
    #         location_success1, shape_success1 = find_image_on_screen(templates["success1"])
    #         location_success2, shape_success2 = find_image_on_screen(templates["success2"])
            
    #         if location_success1 or location_success2:
    #             found_location = location_success1 if location_success1 else location_success2
    #             print(f"找到success图片位置: {found_location}")
    #             move_and_record_images(url)
    #             success_found = True
    #             break
                
    #         time.sleep(0.5)  # 短暂等待后再次尝试
            
    #     if not success_found:
    #         print("5秒内未找到success图片")

if __name__ == '__main__':
    main()