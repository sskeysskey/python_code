# 各种前置导入

import csv
import datetime
from time import sleep

            # 计算中心坐标
            #center_x = (location[0] + shape[1] // 2) // 2
            #center_y = (location[1] + shape[0] // 2) // 2
            # 鼠标点击中心坐标
            #pyautogui.click(center_x, center_y)
            #sleep(0.5)

            # 弹窗提示
            #root = tk.Tk()
            #root.withdraw()  # 隐藏主窗口
            #messagebox.showinfo("操作结果", "已找到并点击图片，然后移动并再次点击了指定位置")

# 将新内容追加到文件末尾，不覆盖
output_file_path = "/Users/yanzhang/Documents/TopGainer.txt"
with open(output_file_path, 'a') as file:
    file.write(new_content + '\n') # 追加内容并在末尾添加换行符

# 将新内容写入文件，覆盖原有内容
output_file_path = "/Users/yanzhang/Documents/TopGainer.txt"
with open(output_file_path, 'w') as file:
    file.write(new_content)

#————————————————————————————————————————————————————————————————————————————————————————
# 点击economist的log in按钮
try:
    # 定位登录链接并点击
    login_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ds-navigation-link[href='/api/auth/login']")))
    login_link.click()
except Exception as e:
    print("登录异常:", e)

# 等待100秒
sleep(110)

try:
    # 使用 WebDriverWait 等待 'Accept all cookies' 按钮变为可点击状态
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
    print("已点击 'Accept all cookies' 按钮")
except Exception as e:
    print(f"点击 'Accept all cookies' 按钮时出错: {e}")

#————————————————————————————————————————————————————————————————————————————————————————
# 智能等待广告弹窗出现
try:
    # 等待 iframe 加载完成
    WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "offer_a6474dcdd142dea508c5-0")))
    print("已进入iframe里面")
    
    # 在 iframe 中等待关闭叉按钮可点击并点击它
    xpath = "//button[contains(@class, 'pn-article_close') and contains(@class, 'ng-scope')]"
    close_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    
    # 切换回主文档
    driver.switch_to.default_content()

except Exception as e:
    print("尝试点击 iframe 中的 关闭叉 出错", e)
    driver.switch_to.default_content()

# 智能等待弹窗出现
try:
    # 等待 iframe 加载完成
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "sp_message_iframe_921614")))
    
    # 在 iframe 中等待“Accept all”按钮可点击并点击它
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Accept all']"))).click()
    print("已点击 iframe 中的接受 cookie 按钮")
    
    # 切换回主文档
    driver.switch_to.default_content()

except Exception as e:
    print("尝试点击 iframe 中的 cookie 同意按钮时出现错误:", e)
    driver.switch_to.default_content()

#————————————————————————————————————————————————————————————————————————————————————————
#先找A，直到找不到A了，再找B，找到B了，执行...
def main():
    a_template_path = '/Users/yanzhang/Documents/python_code/Resource/poe_stop.png'  # A图片的实际路径
    b_template_path = '/Users/yanzhang/Documents/python_code/Resource/poe_more.png'  # B图片的实际路径
    
    # 持续寻找A图片
    while True:
        location, shape = find_image_on_screen(a_template_path)
        if location:
            print("找到A图片，继续监控...")
            sleep(2)  # 简短暂停再次监控
        else:
            print("A图片未找到，转而寻找B图片...")
            break  # A图片不再出现时，跳出循环，开始寻找B图片
    
    # 寻找B图片
    while True:
        location, shape = find_image_on_screen(b_template_path)
        if location:
            print("找到B图片，执行点击和移动操作...")
            # 计算中心坐标
            center_x = (location[0] + shape[1] // 2) //2
            center_y = (location[1] + shape[0] // 2) //2
            # 鼠标点击中心坐标
            pyautogui.click(center_x, center_y)
            # 如果需要移动鼠标并执行其他操作，可在此添加代码
            # ...
            break  # 执行完毕后退出B图片的循环
        else:
            print("未找到B图片，继续监控...")
            sleep(1)  # 没找到B图片，短暂休息后继续寻找

    print("程序执行完毕，退出。")

#————————————————————————————————————————————————————————————————————————————————————————
    # 让用户输入模板图片的路径
    template_path = input("请输入模板图片的完整路径：")
    # 让用户输入截图保存的路径
    screenshot_path = input("请输入截图保存的完整路径：")
    
    # 确保提供的路径是有效的
    try:
        with open(template_path, 'r') as file:
            pass
    except IOError:
        print("无法打开模板图片，请检查路径是否正确。")
        return

#————————————————————————————————————————————————————————————————————————————————————————
    if date_found:
        # 弹窗询问用户操作
        response = messagebox.askyesnocancel("内容检查", f"今天已经爬取过一次了 {formatted_date} 【Yes】打开文件，【No】再次爬取", parent=root)
        if response is None:
            # 用户选择取消或按了ESC键
            print("用户取消操作。")
        elif response:
            # 用户选择“是”，打开当前html文件
            open_html_file(old_file_path)
            print(f"找到匹配当天日期的内容，打开文件：{old_file_path}")
            sys.exit(0)  # 安全退出程序
        else:
            # 用户选择“否”，继续执行后续代码进行重新爬取
            print("用户选择重新爬取，继续执行程序。")
    else:
        response = messagebox.askyesnocancel("内容检查", "没有找到今天的内容，【Yes】打开文件，【No】再次爬取", parent=root)
        if response is None:
            # 用户选择取消或按了ESC键
            print("用户取消操作。")
            sys.exit(0)  # 安全退出程序
        elif response:
            # 用户选择打开文件
            os.system(f'open "{old_file_path}"')  # 假设在macOS上打开文件
            print(f"用户选择打开文件：{old_file_path}")
            sys.exit(0)  # 安全退出程序
        else:
            # 用户选择不打开，可能需要进行其他操作
            print("用户选择不打开文件，继续执行程序。")

#————————————————————————————————————————————————————————————————————————————————————————
# 如果你确实需要控制按钮的布局和默认选项，你可能需要放弃使用messagebox模块，而是自定义一个对话框。
# 下面是一个简单的例子，展示了如何使用Tkinter创建一个自定义对话框，其中"Yes"按钮在左边，"No"按钮在右边，并且"Yes"被默认选中
import tkinter as tk
from tkinter import ttk

def custom_askyesno(title, message, parent):
    # 创建一个顶层窗口
    popup = tk.Toplevel(parent)
    popup.grab_set()  # 使对话框成为模态
    popup.title(title)

    # 显示消息
    message_label = ttk.Label(popup, text=message)
    message_label.pack(pady=(10, 10), padx=10)

    # 创建一个变量来存储用户的选择
    user_choice = tk.BooleanVar(value=True)

    # 创建"Yes"和"No"按钮
    yes_button = ttk.Button(popup, text="Yes", command=lambda: user_choice.set(True))
    no_button = ttk.Button(popup, text="No", command=lambda: user_choice.set(False))

    # 按钮布局："Yes"在左边，"No"在右边
    yes_button.pack(side="left", padx=(10, 5), pady=10)
    no_button.pack(side="right", padx=(5, 10), pady=10)

    # 等待用户作出选择
    popup.wait_window()

    return user_choice.get()

# 主窗口
root = tk.Tk()

# 使用自定义的对话框
response = custom_askyesno("内容检查", "没有新内容\n\n【Yes】打开文件，【No】结束程序", root)

if response:
    # 用户选择“Yes”，执行相关操作
    print("用户选择了'Yes'")
else:
    # 用户选择“No”，执行相关操作
    print("用户选择了'No'")

root.mainloop()
#————————————————————————————————————————————————————————————————————————————————————————
#terminal 指令
#sed -i '' 's/\([0-9]\{4\}\)\.\([0-9]\{2\}\)\.\([0-9]\{2\}\)_/\1_\2_\3_/' /Users/yanzhang/Documents/News/wsj.html
#————————————————————————————————————————————————————————————————————————————————————————
#备份用，原来在爬虫economist代码里的,在添加了七天过滤功能之前的
# 查找旧的 html 文件
file_pattern = "/Users/yanzhang/Documents/News/economist.html"
old_file_list = glob.glob(file_pattern)

if not old_file_list:
    print("未找到符合条件的旧文件。")
    # 处理未找到旧文件的情况
else:
    # 选择第一个找到的文件（您可能需要进一步的逻辑来选择正确的文件）
    old_file_path = old_file_list[0]

    # 读取旧文件中的所有内容
    old_content = []
    with open(old_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        rows = soup.find_all('tr')[1:]  # 跳过标题行
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:  # 确保行有足够的列
                date = cols[0].text.strip()
                title_column = cols[1]
                title = title_column.text.strip()
                # 从标题所在的列中提取链接
                link = title_column.find('a')['href'] if title_column.find('a') else None
                old_content.append([date, title, link])
#————————————————————————————————————————————————————————————————————————————————————————
# 检查 soldout1.png 是否存在于屏幕上
def check_soldout1_image():
    remaining_template_path = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout1.png'  # 替换为你的remaining.png图片实际路径
    location, shape = find_image_on_screen(remaining_template_path, threshold=0.9)
    return bool(location)

# 检查 soldout2.png 是否存在于屏幕上
def check_soldout2_image():
    remaining_template_path = '/Users/yanzhang/Documents/python_code/Resource/claude_soldout2.png'  # 替换为你的remaining.png图片实际路径
    location, shape = find_image_on_screen(remaining_template_path, threshold=0.9)
    return bool(location)

# 检查 soldout1.png 是否存在于屏幕上
if not check_soldout1_image():
    # 如果存在，则写文件
    if check_soldout2_image():
        with open(stop_signal_path, 'w') as signal_file:
            signal_file.write('stop')
else:
    with open(stop_signal_path, 'w') as signal_file:
        signal_file.write('stop')
    # 如果soldout.png不存在，则按原步骤执行
break
#————————————————————————————————————————————————————————————————————————————————————————
# 将修改后的内容写回剪贴板
pyperclip.copy(modified_content)
#————————————————————————————————————————————————————————————————————————————————————————
# 判断是否只有一行内容
if len(non_empty_lines) == 1:
    modified_content = clipboard_content
else:
    # 判断第一句是否以“首先”或“第一”开头
    first_sentence_start_with_special = non_empty_lines and \
        (non_empty_lines[0].startswith('首先') or non_empty_lines[0].startswith('第一'))

    # 计算非空行中以数字或符号开头的行数
    num_start_with_digit_symbol_or_chinese_char = sum(bool(re.match(r'^[\d\W]|^第', line)) for line in non_empty_lines)

    # 判断是否超过50%
    if num_start_with_digit_symbol_or_chinese_char > len(non_empty_lines) / 2:
        # 判断最后一行是否以数字或“第”字开头
        if not non_empty_lines[-1].startswith(('第',)) and not re.match(r'^\d', non_empty_lines[-1]):
            # 如果不是，则剪贴板中第一行和最后一句都删除
            modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):-1])
        else:
            # 如果是，则只删除第一行
            modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])
    else:
        # 如果不足50%，则只删除第一句（除非第一句以“首先”或“第一”开头）
        modified_content = '\n'.join(non_empty_lines[(0 if first_sentence_start_with_special else 1):])
#————————————————————————————————————————————————————————————————————————————————————————
#正则表达式备份
url_pattern = re.compile(r'(http[s]?://|www\.)[^ \n]*|[^ \n]*\.com')
url_pattern = re.compile(r'(http[s]?://|www\.)[^ \n]*|\s[^ \n]*\.com[^ \n]*(?=\s|$)')
url_pattern = re.compile(r'([^ \n]*http[s]?://[^ \n]*(?=\s|$)|[^ \n]*www\.[^ \n]*(?=\s|$)|[^ \n]*\.com[^ \n]*(?=\s|$))')

# 正则表达式，匹配http://, https://或www.开头，直到空格或换行符的字符串
url_pattern = re.compile(
    r'([^ \n]*http[s]?://[^ \n]*(?=\s|$)|'
    r'[^ \n]*www\.[^ \n]*(?=\s|$)|'
    r'[^ \n]*\.(com|gov|edu|cn|us)[^ \n]*(?=\s|$))'
)
#————————————————————————————————————————————————————————————————————————————————————————
template_stop = '/Users/yanzhang/Documents/python_code/Resource/Mistral_stop.png'
template_copy = '/Users/yanzhang/Documents/python_code/Resource/Mistral_copy.png'

found_stop = True
while found_stop:
    location, shape = find_image_on_screen(template_stop)
    if location:
        print("找到thumbup图了，准备下一步...")
        pyautogui.scroll(-80)
        sleep(1) # 继续监控
    else:
        print("没找到图片，继续执行...")
        found_stop = False

found_copy = False
timeout_copy = time.time() + 5
while not found_copy and time.time() < timeout_copy:
    location, shape = find_image_on_screen(template_copy)
    if location:
        print("找到copy图了，准备点击copy...")
        # 计算中心坐标
        center_x = (location[0] + shape[1] // 2) // 2
        center_y = (location[1] + shape[0] // 2) // 2
        
        # 鼠标点击中心坐标
        pyautogui.click(center_x, center_y)
        found_copy = True
    else:
        print("没找到图片，继续执行...")
        sleep(1)

if not found_copy:
    print("在5秒内未找到copy_success图片，退出程序。")
    sys.exit()
#————————————————————————————————————————————————————————————————————————————————————————
import pytesseract
from PIL import ImageGrab
import cv2
import numpy as np

def find_text_on_screen(text_to_find):
    # 捕获全屏
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    # 对图像进行灰度化，这通常有助于OCR识别
    gray_screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

    # 使用Tesseract进行OCR文本识别
    detected_text = pytesseract.image_to_string(gray_screenshot, lang='chi_sim+eng')
    
    # 检查所需文本是否在OCR结果中
    if text_to_find in detected_text:
        print(f"Found text: '{text_to_find}' on the screen.")
        # 这里可以进一步实现定位文本的位置
        # ...
    else:
        print(f"Text: '{text_to_find}' not found on the screen.")

find_text_on_screen("要查找的文本")
#————————————————————————————————————————————————————————————————————————————————————————
def search_files(directories, keyword):
    matched_files = {}  # 修改此处为字典
    # 将关键字转换为小写，以实现大小写不敏感的搜索
    keyword_lower = keyword.lower()

    for directory in directories:
        matched_files[directory] = []
        # 使用os.walk()遍历目录树
        for root, dirs, files in os.walk(directory):
            # 检查目录名是否以.workflow结尾
            for dir_name in dirs:
                if dir_name.endswith('.workflow'):
                    workflow_path = os.path.join(root, dir_name)
                    # 对于.workflow目录，特别处理
                    try:
                        wflow_path = os.path.join(workflow_path, 'contents/document.wflow')
                        with open(wflow_path, 'r') as file:
                            content = file.read().lower()  # 将内容转换为小写
                        if keyword_lower in content:
                            matched_files[directory].append(os.path.relpath(workflow_path, directory))
                    except Exception as e:
                        print(f"Error reading {wflow_path}: {e}")
            # 遍历文件
            for name in files:
                item_path = os.path.join(root, name)
                if item_path.endswith('.scpt'):
                    # 对于.scpt文件，使用osascript命令来获取脚本内容
                    try:
                        content = subprocess.check_output(['osadecompile', item_path], text=True).lower()  # 将内容转换为小写
                        if keyword_lower in content:
                            matched_files[directory].append(os.path.relpath(item_path, directory))
                    except Exception as e:
                        print(f"Error decompiling {item_path}: {e}")
                elif item_path.endswith('.txt') or item_path.endswith('.py'):
                    # 对于.txt文件和.py文件，直接读取内容
                    try:
                        with open(item_path, 'r') as file:
                            content = file.read().lower()  # 将内容转换为小写
                        if keyword_lower in content:
                            matched_files[directory].append(os.path.relpath(item_path, directory))
                    except Exception as e:
                        print(f"Error reading {item_path}: {e}")
    return matched_files
    #————————————————————————————————————————————————————————————————————————————————————————