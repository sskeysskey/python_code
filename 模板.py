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