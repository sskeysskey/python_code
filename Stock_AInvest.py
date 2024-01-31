import cv2
import os
import pyperclip
import pyautogui
from time import sleep

def capture_screen():
    # 定义截图路径
    screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
    # 使用pyautogui截图并直接保存
    pyautogui.screenshot(screenshot_path)
    # 读取刚才保存的截图文件
    screenshot = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    # 确保screenshot已经正确加载
    if screenshot is None:
        raise FileNotFoundError(f"截图未能正确保存或读取于路径 {screenshot_path}")
    # 返回读取的截图数据
    return screenshot

# 查找图片
def find_image_on_screen(template_path, threshold=0.9):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"模板图片未能正确读取于路径 {template_path}")
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # 释放截图和模板图像以节省内存
    del screen
    if max_val >= threshold:
        return max_loc, template.shape
    else:
        return None, None

def remove_even_lines_from_clipboard():
    blacklist_file_path = "/Users/yanzhang/Documents/python_code/Resource/blacklist_topgainer.txt"
    
    # 从剪贴板获取内容
    clipboard_content = pyperclip.paste()
    
    # 按行分割内容成为一个列表
    lines = clipboard_content.split('\n')
    
    # 保留奇数行
    odd_lines = [line for index, line in enumerate(lines) if index % 2 == 0]

    # 读取黑名单文件的内容，并分割成行
    with open(blacklist_file_path, 'r') as file:
        blacklist = file.read().split('\n')

    # 移除与黑名单匹配的行
    filtered_lines = [line for line in odd_lines if line not in blacklist]
    
    # 将处理后的内容转换回字符串
    new_content = '\n'.join(filtered_lines)

    # 将新内容复制回剪贴板
    pyperclip.copy(new_content)

# 主函数
def main():
    try:
        template_path = '/Users/yanzhang/Documents/python_code/Resource/OCR_copy.png'  # 替换为你PNG图片的实际路径
        # 提供黑名单文件的绝对路径
        while True:
            location, shape = find_image_on_screen(template_path)
            if location:
                # 计算中心坐标
                center_x = (location[0] + shape[1] // 2) // 2
                center_y = (location[1] + shape[0] // 2) // 2
                
                # 鼠标点击中心坐标
                pyautogui.click(center_x, center_y)

                sleep(1)  # 简短暂停
                remove_even_lines_from_clipboard()
                break  # 图片消失后退出循环
                
            else:
                print("未找到A图片，继续监控...")
                sleep(1)  # 简短暂停再次监控
    finally:
        screenshot_path = '/Users/yanzhang/Documents/python_code/Resource/screenshot.png'
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print("截图文件已删除。")

if __name__ == '__main__':
    main()