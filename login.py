from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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

    # 直接使用JavaScript查找和点击按钮，从测试结果看这个方法是有效的
    try:
        driver.execute_script("Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('登录')).click()")
        print('使用JavaScript查找并点击登录按钮')
    except Exception as e:
        print(f'JavaScript点击失败: {str(e)}')
        # 如果JavaScript方法失败，尝试备用方法
        try:
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            found = False
            for button in buttons:
                if '登录' in button.text:
                    button.click()
                    print(f'通过遍历找到并点击: {button.text}')
                    found = True
                    break
            
            if not found:
                print('无法找到登录按钮')
        except Exception as e:
            print(f'遍历按钮失败: {str(e)}')
    
    print('正在等待登录对话框')
    # 等待登录对话框出现
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]'))
    )

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

    # 等待页面完全加载
    time.sleep(3)  # 添加额外等待时间

    # 使用更精确的选择器和显式等待
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="invite-code"]'))
    )

    # 获取所有邀请码容器
    invite_containers = driver.find_elements(By.CSS_SELECTOR, 'div[class*="invite-code"]')
    print(f'找到 {len(invite_containers)} 个邀请码容器')

    # 确保页面完全加载
    time.sleep(2)

    # 首先尝试使用 JavaScript 方法获取
    js_success = False
    try:
        elements = driver.execute_script("""
            return Array.from(document.querySelectorAll(".invite-code-item")).map(el => el.innerText);
        """)
        
        if elements:
            print("使用 JavaScript 方法获取邀请码")
            for element_text in elements:
                try:
                    code, status = element_text.split('\n')
                    if code and status:
                        print(f'邀请码: {code}, 状态: {status}')
                        js_success = True
                except Exception as e:
                    print(f'处理邀请码文本时出错: {str(e)}')
    except Exception as e:
        print(f'JavaScript 方法获取失败，尝试备用方法: {str(e)}')

    # 如果 JavaScript 方法成功，跳过 Selenium 方法
    if js_success:
        print("成功使用 JavaScript 方法获取邀请码")
    else:
        # 使用 Selenium 方法作为备用
        for container in invite_containers:
            try:
                # 使用 JavaScript 滚动到元素位置，确保元素可见
                driver.execute_script("arguments[0].scrollIntoView(true);", container)
                time.sleep(0.5)  # 短暂等待滚动完成

                # 尝试多个可能的选择器
                code = None
                status = None

                # 尝试不同的选择器组合
                selectors = [
                    ('.items-center.coz-fg-plus', 'div > div > div > div:nth-child(2) > div > span'),
                    ('div[class*="invite-code"] > div.coz-fg-plus', 'div[class*="invite-code"] > div > button > div > span')
                ]

                for code_selector, status_selector in selectors:
                    try:
                        code_element = container.find_element(By.CSS_SELECTOR, code_selector)
                        status_element = container.find_element(By.CSS_SELECTOR, status_selector)
                        code = code_element.text.strip()
                        status = status_element.text.strip()
                        if code and status:
                            break
                    except:
                        continue

                if code and status:
                    print(f'邀请码: {code}, 状态: {status}')
                else:
                    print('未能获取邀请码或状态')

            except Exception as e:
                print(f'处理邀请码元素时出错: {str(e)}')
                continue

    print("登录完成")

finally:
    driver.quit()
    print("浏览器已关闭")