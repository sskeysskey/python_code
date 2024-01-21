import cv2
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

def click_image(location, shape):
    # 计算中心坐标
    center_x = (location[0] + shape[1] // 2) // 2
    center_y = (location[1] + shape[0] // 2) // 2
    # 鼠标点击中心坐标
    pyautogui.click(center_x, center_y)

# 主函数
def main():
    template_path1 = '/Users/yanzhang/Documents/python_code/Resource/claude_new_chat.png'
    template_path2 = '/Users/yanzhang/Documents/python_code/Resource/claude_message.png'
    while True:
        location, shape = find_image_on_screen(template_path1)
        if location:
            click_image(location, shape)
            break  # 图片消失后退出循环
        else:
            print("未找到A图片，继续监控...")
            sleep(1)  # 简短暂停再次监控

    # 点击第一张图片后，检测第二张图片是否出现
    while True:
        location, shape = find_image_on_screen(template_path2)
        if location:
            break
        else:
            print("未找到第二张图片，继续监控...")
            sleep(1)

if __name__ == '__main__':
    main()