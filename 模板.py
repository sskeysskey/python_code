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