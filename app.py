from fastapi import FastAPI, Request, HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi.staticfiles import StaticFiles
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
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
from fastapi.responses import HTMLResponse, JSONResponse
from functools import lru_cache

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
CACHE_TTL = 300  # 缓存有效期5分钟
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

# 添加缓存装饰器
@lru_cache(maxsize=1)
def get_cached_data():
    """获取缓存的数据"""
    return load_data()

def invalidate_cache():
    """使缓存失效"""
    get_cached_data.cache_clear()

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

# 设置一个重试装饰器
def retry(max_tries=3, delay_seconds=5):
    def decorator_retry(func):
        def wrapper(*args, **kwargs):
            tries = 0
            while tries < max_tries:
                try:
                    return func(*args, **kwargs)
                except (WebDriverException, TimeoutException) as e:
                    tries += 1
                    if tries == max_tries:
                        logger.error(f"重试{max_tries}次后仍然失败: {str(e)}")
                        raise
                    logger.warning(f"操作失败，{delay_seconds}秒后尝试第{tries+1}次重试: {str(e)}")
                    time.sleep(delay_seconds)
            return None
        return wrapper
    return decorator_retry

# 安全解析邀请码文本
def parse_invite_code_text(text):
    """安全解析邀请码文本，处理各种可能的格式"""
    try:
        # 记录原始文本用于调试
        logger.debug(f"解析邀请码文本: {text}")
        
        # 去除字符串前后的空白
        text = text.strip()
        
        # 按行分割
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 检查行数
        if not lines:
            return None, None
        
        # 如果只有一行，尝试分解
        if len(lines) == 1:
            # 可能格式: "CODE 已激活" 或 "CODE, 已激活"
            parts = lines[0].split(' ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
            
            # 尝试按逗号分割
            parts = lines[0].split(',', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
            
            # 无法分割，只返回代码
            return lines[0], "未知状态"
        
        # 如果有多行，第一行是代码，后面的合并作为状态
        code = lines[0]
        status = ' '.join(lines[1:])
        return code, status
    
    except Exception as e:
        logger.error(f"解析邀请码文本出错: {str(e)}, 原文本: '{text}'")
        # 返回默认值
        return text, "未知状态"

# 获取邀请码
@retry(max_tries=3, delay_seconds=5)
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
    chrome_options.add_argument('--disable-gpu')
    # 移除可能导致稳定性问题的选项
    # chrome_options.add_argument('--memory-pressure-off')
    # chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-dev-tools')
    # 使用normal替代eager，提高页面加载稳定性
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    if chrome_path:
        chrome_options.binary_location = chrome_path
    
    driver = None
    try:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置页面加载超时
        driver.set_page_load_timeout(60)
        # 设置脚本执行超时
        driver.set_script_timeout(30)
        
        update_status_step("打开登录页面")
        driver.get("https://www.coze.cn/space-preview?")
        
        wait = WebDriverWait(driver, 30)
        
        update_status_step("等待页面加载")
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        # 添加额外等待，确保页面所有元素都加载完毕
        time.sleep(3)

        update_status_step("点击登录按钮")
        # 使用JavaScript方法点击登录按钮（已验证有效）
        try:
            driver.execute_script("Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('登录')).click()")
            logger.info("使用JavaScript查找并点击登录按钮")
        except Exception as e:
            logger.error(f"JavaScript点击失败: {str(e)}")
            # 尝试备用方法
            try:
                buttons = driver.find_elements(By.TAG_NAME, 'button')
                found = False
                for button in buttons:
                    if '登录' in button.text:
                        button.click()
                        logger.info(f"通过遍历找到并点击: {button.text}")
                        found = True
                        break
                
                if not found:
                    logger.error("无法找到登录按钮")
                    # 添加截图记录页面状态
                    screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"已保存错误截图到 {screenshot_path}")
                    raise Exception("无法找到登录按钮")
            except Exception as e:
                logger.error(f"遍历按钮失败: {str(e)}")
                raise

        update_status_step("等待登录对话框出现")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')))

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
        time.sleep(5)  # 增加延迟时间，确保登录完全完成

        update_status_step("点击快速开始")
        try:
            quick_start_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '快速开始')]"))
            )
            quick_start_button.click()
            # 添加点击后的短暂等待
            time.sleep(2)
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
            # 添加点击后的短暂等待
            time.sleep(2)
        except Exception as e:
            logger.warning(f"点击立即邀请按钮失败: {str(e)}")
            # 可能已经在邀请码页面
            pass

        update_status_step("获取邀请码信息")
        # 等待页面完全加载
        time.sleep(5)  # 增加等待时间

        # 首先尝试使用 JavaScript 方法获取
        codes = []
        try:
            elements = driver.execute_script("""
                return Array.from(document.querySelectorAll(".invite-code-item")).map(el => el.innerText);
            """)
            
            if elements:
                logger.info("使用 JavaScript 方法获取邀请码")
                for element_text in elements:
                    try:
                        # 使用安全解析函数
                        code, status = parse_invite_code_text(element_text)
                        if code:
                            logger.info(f'邀请码: {code}, 状态: {status}')
                            codes.append({
                                'code': code.strip(),
                                'status': status.strip()
                            })
                    except Exception as e:
                        logger.error(f'处理邀请码文本时出错: {str(e)}')
        except Exception as e:
            logger.warning(f'JavaScript 方法获取失败，尝试备用方法: {str(e)}')

        # 如果 JavaScript 方法没有获取到数据，使用 Selenium 方法
        if not codes:
            logger.info("使用 Selenium 方法获取邀请码")
            # 等待邀请码容器出现
            try:
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="invite-code"]'))
                )
                
                # 获取所有邀请码容器
                invite_containers = driver.find_elements(By.CSS_SELECTOR, 'div[class*="invite-code"]')
                logger.info(f'找到 {len(invite_containers)} 个邀请码容器')

                for container in invite_containers:
                    try:
                        # 使用 JavaScript 滚动到元素位置
                        driver.execute_script("arguments[0].scrollIntoView(true);", container)
                        time.sleep(0.5)

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
                                if code:  # 只要有code就添加，不强制要求status
                                    codes.append({
                                        'code': code,
                                        'status': status if status else "未知状态"
                                    })
                                    break
                            except:
                                continue

                    except Exception as e:
                        logger.error(f'处理邀请码元素时出错: {str(e)}')
                        continue
            except Exception as e:
                logger.error(f'定位邀请码容器时出错: {str(e)}')
                # 保存截图记录页面状态
                screenshot_path = f"error_invite_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"已保存邀请码页面错误截图到 {screenshot_path}")

        if not codes:
            logger.warning("未找到任何邀请码")
            
        return codes
            
    except Exception as e:
        error_msg = f"获取邀请码过程中出错: {str(e)}"
        logger.error(error_msg)
        # 捕获异常后尝试保存截图
        try:
            if driver:
                screenshot_path = f"error_exception_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"已保存异常时截图到 {screenshot_path}")
        except:
            pass
        raise HTTPException(status_code=500, detail=error_msg)
        
    finally:
        if driver:
            try:
                logger.info("正在关闭浏览器...")
                driver.quit()
                logger.info("浏览器已关闭")
                
                # 强制检查潜在的残留进程 (针对ChromeDriver)
                if platform.system().lower() == "linux":
                    try:
                        os.system("pkill -f chromedriver")
                        os.system("pkill -f chrome")
                        logger.info("已清理可能残留的Chrome进程")
                    except Exception as e:
                        logger.error(f"清理Chrome进程时出错: {str(e)}")
                elif platform.system().lower() == "darwin":  # macOS
                    try:
                        os.system("pkill -f 'Google Chrome'")
                        os.system("pkill -f chromedriver")
                        logger.info("已清理可能残留的Chrome进程")
                    except Exception as e:
                        logger.error(f"清理Chrome进程时出错: {str(e)}")
                elif platform.system().lower() == "windows":
                    try:
                        os.system("taskkill /f /im chromedriver.exe")
                        os.system("taskkill /f /im chrome.exe")
                        logger.info("已清理可能残留的Chrome进程")
                    except Exception as e:
                        logger.error(f"清理Chrome进程时出错: {str(e)}")
                
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")
                # 如果常规关闭失败，尝试更激进的方法
                try:
                    if hasattr(driver, 'service') and driver.service.process:
                        driver.service.process.kill()
                        logger.info("已强制终止ChromeDriver进程")
                except Exception as e:
                    logger.error(f"强制终止浏览器进程时出错: {str(e)}")

# 修改 load_data 函数
def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {"codes": [], "last_update": None, "next_update": None}

# 修改 save_data 函数
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    invalidate_cache()  # 保存数据时使缓存失效

# 获取一个未激活的邀请码并将其状态修改为已激活
def get_and_activate_invite_code():
    data = load_data()
    codes = data.get("codes", [])
    
    # 查找未激活的邀请码
    for i, code_item in enumerate(codes):
        # 检查状态是否包含"未激活"字样
        if "未激活" in code_item.get("status", ""):
            # 获取邀请码数据
            code_data = {
                "code": code_item["code"],
                "status": code_item["status"],
                "source": code_item.get("source", "未知")
            }
            
            # 更新状态为已激活
            codes[i]["status"] = "已激活"
            data["codes"] = codes
            save_data(data)
            
            logger.info(f"邀请码 {code_data['code']} 已被激活")
            return code_data
    
    # 没有找到未激活的邀请码
    return None

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

# 修改 API 端点
@app.get("/api/codes")
def get_codes():
    return get_cached_data()

@app.get('/api/invite_codes')
async def get_invite_codes_api():
    """获取邀请码数据"""
    data = get_cached_data()
    return {
        "is_updating": update_status["is_updating"],
        "current_step": update_status["current_step"],
        "last_update_time": update_status["last_update_time"],
        "next_update_time": update_status["next_update_time"],
        "last_error": update_status["last_error"],
        "codes": data.get("codes", [])
    }

@app.get('/api/get_invite_code')
async def get_unused_invite_code():
    """获取一个未激活的邀请码并将其状态改为已激活"""
    # 先从现有数据中尝试获取未激活邀请码
    invite_code = get_and_activate_invite_code()
    
    # 如果找到了未激活的邀请码，直接返回
    if invite_code:
        return JSONResponse(content={
            "success": True,
            "code": invite_code["code"],
            "status": "已激活",  # 新状态
            "source": invite_code["source"],
            "message": "获取邀请码成功"
        })
    
    # 如果没有找到未激活的邀请码，触发更新
    if update_status["is_updating"]:
        return JSONResponse(
            status_code=423,
            content={
                "success": False,
                "message": "正在更新邀请码数据，请稍后再试",
                "current_step": update_status["current_step"]
            }
        )
    
    try:
        # 启动一个新线程进行更新，不阻塞当前请求
        def update_thread():
            try:
                update_invite_codes()
            except Exception as e:
                logger.error(f"更新线程中出错: {str(e)}")
        
        threading.Thread(target=update_thread, daemon=True).start()
        
        return JSONResponse(
            status_code=202,
            content={
                "success": False,
                "message": "没有可用的邀请码，已触发更新，请稍后再试"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"获取邀请码失败: {str(e)}"
            }
        )

def schedule_jobs():
    """定时任务"""
    logger.info("启动定时任务")
    
    def random_update():
        try:
            data = update_invite_codes()
            if data and data.get("next_update"):
                next_delay = (data["next_update"] - int(datetime.now().timestamp() * 1000)) / 60000
                schedule.clear()
                schedule.every(next_delay).minutes.do(random_update)
        except Exception as e:
            logger.error(f"更新任务出错: {str(e)}")
            # 添加安全兜底，确保即使出错也会在一段时间后重试
            schedule.clear()
            schedule.every(15).minutes.do(random_update)  # 出错后15分钟再尝试

    random_update()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 将检查间隔从1秒改为60秒

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