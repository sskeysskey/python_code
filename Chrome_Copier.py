import cv2
import numpy as np
from PIL import ImageGrab
import os
import sys
from datetime import datetime

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

def write_to_file(url):
    """
    将URL写入指定文件
    """
    file_path = "/Users/yanzhang/Documents/News/article_copier.txt"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 准备写入的内容
    content = f"[{current_time}] {url}\n"
    
    # 以追加模式打开文件
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)

def main():
    # 获取传入的URL参数
    url = sys.argv[1] if len(sys.argv) > 1 else "No URL provided"
    
    # 定义模板路径字典
    template_paths = {
        "failure": "/Users/yanzhang/Documents/python_code/Resource/copier_failure.png"
    }

    # 读取所有模板图片，并存储在字典中
    templates = {}
    for key, path in template_paths.items():
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"模板图片未能正确读取于路径 {path}")
        templates[key] = template

    location_failure, shape_failure = find_image_on_screen(templates["failure"])
    if location_failure:
        print(f"找到图片位置: {location_failure}")
        # 在这里添加写入文件的操作
        write_to_file(url)

if __name__ == '__main__':
    main()