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
    match = re.search('<div class="c">\r\n(.*?)</div>\r\n', resp["response"], re.S)
    msg = match[1] if match else "签到失败"
    print(f"【签到】{msg}")
    return "恭喜你签到成功!" in msg or "您今日已经签到" in msg

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
    # 禁用自动化标志
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options, version_main=150)

    # 使用 CDP 在导航前设置 cookies（比 add_cookie 更可靠）
    if cookie_string.startswith("cookie:"):
        cookie_string = cookie_string[len("cookie:"):]
    cookies = []
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            k, v = k.strip(), v.strip()
            if k and v:
                cookies.append({
                    "name": k, "value": v,
                    "domain": "zodgame.xyz", "path": "/"
                })
    driver.execute_cdp_cmd("Network.setCookies", {"cookies": cookies})

    driver.get("https://zodgame.xyz/")
    WebDriverWait(driver, 240).until(lambda x: x.title != "Just a moment...")

    # 验证登录
    assert not driver.find_elements(By.XPATH, '//a[text()="用户名"]'), \
        "Login fails. Cookie may be expired."
    
    formhash = driver.find_element(By.XPATH, '//input[@name="formhash"]').get_attribute('value')
    assert zodgame_checkin(driver, formhash) and zodgame_task(driver, formhash), \
        "Checkin or tasks failed."
    driver.quit()

if __name__ == "__main__":
    zodgame(sys.argv[1])