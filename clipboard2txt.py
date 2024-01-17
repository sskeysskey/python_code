import pyautogui
import time
import pyperclip
from time import sleep

pyautogui.moveTo(485, 662)
sleep(0.5)
pyautogui.click(button='right')
sleep(0.5)
# 移动鼠标并再次点击
pyautogui.moveRel(110, 118)  # 往左移动110，往下移动118
sleep(0.5)
pyautogui.click()  # 执行点击操作
sleep(1)

# 设置SRT文件的保存路径
srt_file_path = '/Users/yanzhang/Movies/逃不开的经济周期.txt'

# 读取剪贴板内容
clipboard_content = pyperclip.paste()

# 追加剪贴板内容到SRT文件
with open(srt_file_path, 'a', encoding='utf-8-sig') as f:
    f.write(clipboard_content)
    f.write('\n\n')  # 添加两个换行符以创建一个空行