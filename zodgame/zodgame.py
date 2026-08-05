# encoding=utf8
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

def zodgame_checkin(driver, formhash):
    checkin_url = "https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=0"    
    query = """
        (function(){
        var r = new XMLHttpRequest();
        var fd = new FormData();
        fd.append("formhash","%s");
        fd.append("qdxq","kx");
        r.open("POST","%s",false);
        r.withCredentials=true;
        r.send(fd);
        return r;
        })();
        """ % (formhash, checkin_url)
    query = query.replace("\n", "")
    driver.set_script_timeout(240)
    resp = driver.execute_script("return " + query)
    body = resp.get("response", "") or ""
    # 宽松解析：多种分隔符都尝试
    msg = None
    for pat in [r'<div class="c">\s*(.*?)\s*</div>', r'<div class="alert_info">(.*?)</div>', r'<h3[^>]*>(.*?)</h3>']:
        m = re.search(pat, body, re.S)
        if m:
            msg = m.group(1).strip()
            break
    if msg is None:
        msg = re.sub(r'<[^>]+>', '', body).strip()[:100] or "签到失败"
    print(f"【签到】{msg}")
    if "恭喜" in body or "已经签到" in body or "明天再来" in body:
        return True
    print(f"【Log】原始响应: {body[:200]}")
    return False

def zodgame_task(driver, formhash):
    def clear_handles(driver, main_handle):
        for h in driver.window_handles[:]:
            if h != main_handle:
                driver.switch_to.window(h); driver.close()
        driver.switch_to.window(main_handle)
      
    def show_reward(driver):
        driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
        try:
            WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")
            reward = driver.find_element(By.XPATH, '//li[contains(text(), "点币: ")]').text
            print(f"【Log】{reward}")
        except: pass

    driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
    WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")

    if driver.find_elements(By.XPATH, '//font[text()="开始参与任务"]'):
        driver.get(f"https://zodgame.xyz/plugin.php?id=jnbux:jnbux&do=join&formhash={formhash}")
        WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")
        driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
        WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")

    tasks = driver.find_elements(By.XPATH, '//a[text()="参与任务"]')
    if not tasks:
        print("【任务】所有任务均已完成。")
        return True

    success = True
    handle = driver.current_window_handle
    for idx, a in enumerate(tasks):
        oc = a.get_attribute("onclick")
        try:
            func = re.search(r"openNewWindow(.*?)\(\)", oc, re.S)[0]
            script = driver.find_element(By.XPATH, f'//script[contains(text(), "{func}")]').get_attribute("text")
            task_url = re.search(r'window\.open\("(.*)", "newwindow"\)', script, re.S)[1]
            driver.execute_script(f'window.open("https://zodgame.xyz/{task_url}")')
            driver.switch_to.window(driver.window_handles[-1])
            try:
                WebDriverWait(driver, 240).until(lambda x: x.find_elements(By.XPATH, '//div[text()="成功！"]'))
            except:
                print(f"【Log】任务 {idx+1} 广告页超时")
            try:
                ck = re.search(r"showWindow\('check', '(.*)'\);", oc, re.S)[1]
                driver.get(f"https://zodgame.xyz/{ck}")
                WebDriverWait(driver, 240).until(
                    lambda x: len(x.find_elements(By.XPATH, '//p[contains(text(), "检查成功")]')) > 0
                    or x.title == "BUX广告点击赚积分 - ZodGame论坛 - Powered by Discuz!"
                )
                print(f"【任务】任务 {idx+1} 成功。")
            except:
                print(f"【Log】任务 {idx+1} 确认页异常")
        except Exception as e:
            success = False
            print(f"【任务】任务 {idx+1} 失败", type(e).__name__)
        finally:
            clear_handles(driver, handle)
    show_reward(driver)
    return success

def zodgame(cookie_string):
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options, version_main=150)

    if cookie_string.startswith("cookie:"):
        cookie_string = cookie_string[len("cookie:"):]
    cookie_dict = [ 
        {"name": x.split('=')[0].strip(), "value": x.split('=')[1].strip()} 
        for x in cookie_string.split(';')
    ]

    driver.get("https://zodgame.xyz/")
    driver.delete_all_cookies()
    for cookie in cookie_dict:
        if cookie["name"] in ["qhMq_2132_saltkey", "qhMq_2132_auth"]:
            try:
                driver.add_cookie({
                    "domain": "zodgame.xyz",
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "path": "/",
                })
            except Exception as e:
                print(f"【Log】注入 cookie {cookie['name']} 失败: {e}")
    
    driver.get("https://zodgame.xyz/")
    WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")

    assert not driver.find_elements(By.XPATH, '//a[text()="用户名"]'), \
        "Login fails. Cookie may be expired."
    
    formhash = driver.find_element(By.XPATH, '//input[@name="formhash"]').get_attribute('value')
    # 签到和任务分开断言，避免短路导致任务不执行
    ok_checkin = zodgame_checkin(driver, formhash)
    ok_task = zodgame_task(driver, formhash)
    driver.quit()
    sys.exit(0 if (ok_checkin or ok_task) else 1)

if __name__ == "__main__":
    zodgame(sys.argv[1])