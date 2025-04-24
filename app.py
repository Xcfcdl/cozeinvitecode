from fastapi import FastAPI, Request, HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi.staticfiles import StaticFiles
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import schedule
import time
import threading
import json
import os
import platform
import random
from datetime import datetime, timedelta
from threading import Lock
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
from pathlib import Path
from fastapi.responses import HTMLResponse

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
DATA_FILE = "data/data.json"
os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

# 添加状态跟踪
update_status = {
    "is_updating": False,
    "last_update_time": None,
    "last_error": None,
    "current_step": None,
    "next_update_time": None
}
update_lock = Lock()

def update_status_step(step: str):
    """更新当前执行步骤"""
    global update_status
    update_status["current_step"] = step
    logger.info(f"当前步骤: {step}")

# 获取Chrome和ChromeDriver路径
def get_chrome_paths():
    system = platform.system().lower()
    if system == "darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if not Path(chrome_path).exists():
            chrome_path = None
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
    elif system == "windows":
        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if not Path(chrome_path).exists():
            chrome_path = None
        chromedriver_path = ".\\chromedriver.exe"
    else:  # Linux
        chrome_path = "/usr/bin/google-chrome"
        if not Path(chrome_path).exists():
            chrome_path = None
        chromedriver_path = "/usr/bin/chromedriver"
    
    return chrome_path, chromedriver_path

# 获取邀请码
def get_invite_codes(account_id, password):
    chrome_path, chromedriver_path = get_chrome_paths()
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    if chrome_path:
        chrome_options.binary_location = chrome_path
    
    driver = None
    try:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        update_status_step("打开登录页面")
        driver.get("https://www.coze.cn/space-preview?")
        
        wait = WebDriverWait(driver, 30)
        
        update_status_step("等待页面加载")
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

        update_status_step("点击登录按钮")
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.login-btn--WcinUq6XuYM7snJD'))
        )
        login_button.click()

        update_status_step("切换到账号登录")
        account_login_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#arco-tabs-0-tab-1'))
        )
        account_login_tab.click()

        update_status_step("输入账号信息")
        account_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#Identity_input'))
        )
        account_input.send_keys(account_id)

        password_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#Password_input'))
        )
        password_input.send_keys(password)

        update_status_step("提交登录")
        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#arco-tabs-0-panel-1 > div > div > form > div:nth-child(6) > button'))
        )
        submit_button.click()

        update_status_step("等待登录完成")
        wait.until(EC.url_contains('space'))
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

        # 添加短暂延迟确保页面完全加载
        time.sleep(2)

        update_status_step("点击快速开始")
        try:
            quick_start_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '快速开始')]"))
            )
            quick_start_button.click()
        except Exception as e:
            logger.warning(f"点击快速开始按钮失败: {str(e)}")
            # 尝试直接点击立即邀请按钮
            pass

        update_status_step("点击立即邀请")
        try:
            invite_now_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '立即邀请')]"))
            )
            invite_now_button.click()
        except Exception as e:
            logger.warning(f"点击立即邀请按钮失败: {str(e)}")
            # 可能已经在邀请码页面
            pass

        update_status_step("获取邀请码信息")
        # 等待邀请码元素出现
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.items-center.coz-fg-plus'))
        )
        
        # 获取所有邀请码元素
        invite_codes = driver.find_elements(By.CSS_SELECTOR, '.items-center.coz-fg-plus')
        # 获取所有状态元素
        statuses = driver.find_elements(By.CSS_SELECTOR, 'div.relative > div > div > div > div:nth-child(2) > div > span')

        codes = []
        # 使用 zip 安全地遍历两个列表
        for code_elem, status_elem in zip(invite_codes, statuses):
            try:
                code_text = code_elem.text.strip()
                status_text = status_elem.text.strip()
                if code_text:
                    logger.info(f'邀请码: {code_text}, 状态: {status_text}')
                    codes.append({
                        'code': code_text,
                        'status': status_text
                    })
            except Exception as e:
                logger.error(f"处理邀请码元素时出错: {str(e)}")
                continue
        
        if not codes:
            logger.warning("未找到任何邀请码")
            
        return codes
            
    except Exception as e:
        error_msg = f"获取邀请码过程中出错: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")

# 保存数据到文件
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 从文件加载数据
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"codes": [], "last_update": None, "next_update": None}

# 更新邀请码
def update_invite_codes():
    global update_status
    
    if not update_lock.acquire(blocking=False):
        logger.info("已有更新任务在运行中")
        return
    
    try:
        update_status["is_updating"] = True
        update_status["last_error"] = None
        all_codes = []
        current_time = datetime.now()
        update_time = current_time.isoformat()
        
        # 获取账号1的邀请码
        if os.getenv("ACCOUNT1_ID") and os.getenv("ACCOUNT1_PASSWORD"):
            try:
                codes1 = get_invite_codes(os.getenv("ACCOUNT1_ID"), os.getenv("ACCOUNT1_PASSWORD"))
                if codes1:
                    all_codes.extend([{"code": code["code"], "status": code["status"], "source": "账号1"} for code in codes1])
            except Exception as e:
                error_msg = f"账号1获取邀请码失败: {str(e)}"
                logger.error(error_msg)
                update_status["last_error"] = error_msg
        
        # 获取账号2的邀请码
        if os.getenv("ACCOUNT2_ID") and os.getenv("ACCOUNT2_PASSWORD"):
            try:
                codes2 = get_invite_codes(os.getenv("ACCOUNT2_ID"), os.getenv("ACCOUNT2_PASSWORD"))
                if codes2:
                    all_codes.extend([{"code": code["code"], "status": code["status"], "source": "账号2"} for code in codes2])
            except Exception as e:
                error_msg = f"账号2获取邀请码失败: {str(e)}"
                logger.error(error_msg)
                if not update_status["last_error"]:  # 如果之前没有错误
                    update_status["last_error"] = error_msg
        
        # 生成下次更新时间（10-20分钟之间随机）
        minutes = random.randint(10, 20)
        next_update = current_time + timedelta(minutes=minutes)
        next_update_timestamp = int(next_update.timestamp() * 1000)  # 转换为毫秒时间戳
        
        logger.info(f"下次更新时间设置为 {minutes} 分钟后")
        
        data = {
            "codes": all_codes,
            "last_update": update_time,
            "next_update": next_update_timestamp
        }
        
        save_data(data)
        update_status["last_update_time"] = update_time
        update_status["next_update_time"] = next_update_timestamp
        
        return data
        
    except Exception as e:
        error_msg = f"更新邀请码失败: {str(e)}"
        logger.error(error_msg)
        update_status["last_error"] = error_msg
        raise
    
    finally:
        update_status["is_updating"] = False
        update_status["current_step"] = None
        update_lock.release()

@app.get("/api/codes")
def get_codes():
    return load_data()

@app.get('/api/invite_codes')
async def get_invite_codes_api():
    """获取邀请码数据"""
    data = load_data()
    return {
        "is_updating": update_status["is_updating"],
        "current_step": update_status["current_step"],
        "last_update_time": update_status["last_update_time"],
        "next_update_time": update_status["next_update_time"],
        "last_error": update_status["last_error"],
        "codes": data.get("codes", [])
    }

def schedule_jobs():
    """定时任务"""
    logger.info("启动定时任务")
    
    def random_update():
        try:
            # 执行更新
            data = update_invite_codes()
            if data and data.get("next_update"):
                # 计算下次更新的延迟时间（毫秒转分钟）
                next_delay = (data["next_update"] - int(datetime.now().timestamp() * 1000)) / 60000
                schedule.clear()  # 清除之前的任务
                schedule.every(next_delay).minutes.do(random_update)
        except Exception as e:
            logger.error(f"更新任务出错: {str(e)}")

    # 初始运行
    random_update()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("应用启动，执行初始化更新")
    # 加载已保存的数据
    data = load_data()
    if data:
        update_status["last_update_time"] = data.get("last_update")
        update_status["next_update_time"] = data.get("next_update")
    
    # 启动自动更新线程
    threading.Thread(target=schedule_jobs, daemon=True).start()

# 自定义 HTML 响应处理类
class CustomHTMLResponse(HTMLResponse):
    def __init__(self, content: str, *args, **kwargs):
        # 从环境变量获取 Google Analytics ID
        ga_id = os.getenv('GOOGLE_ANALYTICS_ID', '')
        # 替换模板变量
        content = content.replace('{{ GOOGLE_ANALYTICS_ID }}', ga_id)
        super().__init__(content, *args, **kwargs)

# 自定义静态文件处理
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith('.html'):
            content = await response.body()
            return CustomHTMLResponse(content.decode())
        return response

# 修改静态文件挂载
app.mount("/static", CustomStaticFiles(directory="static"), name="static")
app.mount("/", CustomStaticFiles(directory="static", html=True), name="root")