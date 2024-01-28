import cv2
import pyautogui
import pyperclip
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

def main():
    template_path = '/Users/yanzhang/Documents/python_code/Resource/claude_done_125.png'  # 替换为你PNG图片的实际路径
    while True:
        location, shape = find_image_on_screen(template_path)
        if location:
            # 读取/tmp/segment.txt文件内容
            segment_file_path = '/tmp/segment.txt'
            with open(segment_file_path, 'r', encoding='utf-8-sig') as segment_file:
                segment_content = segment_file.read()

            # 在segment_content后面添加一个换行符
            segment_content += '\n'
            
            # 将读取到的segment_content内容插入在剪贴板内容的最前面
            final_content = segment_content + modified_content

            # 追加处理后的内容到TXT文件
            with open(txt_file_path, 'a', encoding='utf-8-sig') as txt_file:
                txt_file.write(final_content)
                txt_file.write('\n\n')  # 添加两个换行符以创建一个空行

pyautogui.moveTo(485, 662)
sleep(0.5)
pyautogui.click(button='right')
sleep(0.5)
# 移动鼠标并再次点击
pyautogui.moveRel(110, 118)  # 往左移动110，往下移动118
sleep(0.5)
pyautogui.click()  # 执行点击操作
sleep(1)

# 设置txt文件的保存路径
txt_file_path = '/Users/yanzhang/Documents/book.txt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 追加剪贴板内容到txt文件
with open(txt_file_path, 'a', encoding='utf-8-sig') as f:
    f.write(clipboard_content)
    f.write('\n\n')  # 添加两个换行符以创建一个空行