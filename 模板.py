# 各种前置导入
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import datetime
from time import sleep

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