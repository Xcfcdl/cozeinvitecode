from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 读取环境变量
print('开始读取环境变量')
with open('.env', 'r') as f:
    account_id = f.readline().strip().split('=')[1]
    password = f.readline().strip().split('=')[1]
print('环境变量读取完成')

# 配置 Chrome 选项
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')

# 初始化浏览器
print('开始初始化浏览器')
# driver = webdriver.Chrome()
driver = webdriver.Chrome(options=chrome_options)
print('浏览器初始化完成')

try:
    # 打开登录页面
    print('正在打开登录页面')
    driver.get('https://www.coze.cn/space-preview?')
    print('登录页面已打开')

    # 点击登录按钮
    login_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.login-btn--WcinUq6XuYM7snJD'))
    )
    login_button.click()
    print('登录按钮已点击')

    # 等待并点击账号登录tab
    account_login_tab = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#arco-tabs-0-tab-1'))
    )
    account_login_tab.click()
    print('账号登录tab已点击')

    # 输入账号和密码
    account_input = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#Identity_input'))
    )
    account_input.send_keys(account_id)
    print('账号输入完成')

    password_input = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#Password_input'))
    )
    password_input.send_keys(password)
    print('密码输入完成')

    # 提交登录
    submit_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#arco-tabs-0-panel-1 > div > div > form > div:nth-child(6) > button'))
    )
    submit_button.click()
    print('正在提交登录')

    # 等待登录成功跳转
    WebDriverWait(driver, 30).until(
        EC.url_contains('space')
    )

    # 等待并点击快速开始
    quick_start_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '快速开始')]"))
    )
    quick_start_button.click()
    print('正在等待并点击快速开始')

    # 等待并点击立即邀请
    invite_now_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '立即邀请')]"))
    )
    invite_now_button.click()
    print('正在等待并点击立即邀请')

    # 获取邀请码和激活状态信息
    invite_codes = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.items-center.coz-fg-plus'))
    )
    statuses = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.relative > div > div > div > div:nth-child(2) > div > span'))
    )
    print('邀请码和激活状态信息获取完成')

    for i in range(len(invite_codes)):
        print(f'邀请码: {invite_codes[i].text}, 状态: {statuses[i].text}')

    print("登录完成")

finally:
    pass