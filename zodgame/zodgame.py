import os, re, sys, time
from urllib.parse import urljoin
import requests

BASE_URL = 'https://zodgame.xyz'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html,*/*', 'Accept-Language': 'zh-CN,zh;q=0.9'}
HEADERS_FORM = {**HEADERS, 'Content-Type': 'application/x-www-form-urlencoded', 'Origin': BASE_URL}
TIMEOUT = 30

def parse_cookie(s):
    cookies = {}
    for item in s.split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies

def get_formhash(session):
    r = session.get(BASE_URL + '/', headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200: return None
    m = re.search(r'<input\s+type="hidden"\s+name="formhash"\s+value="([^"]+)"', r.text)
    return m.group(1) if m else None

def sign_in(session, formhash):
    data = f'formhash={formhash}&qdxq=shuai'
    r = session.post(f'{BASE_URL}/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1', headers=HEADERS_FORM, data=data, timeout=TIMEOUT)
    if '恭喜' in r.text and '成功' in r.text: print('[✓] 签到成功！'); return True
    if '今日已经签到' in r.text: print('[✓] 今日已签到'); return True
    print(f'[?] {r.text[:80]}'); return False

def do_tasks(session, formhash):
    bux_url = f'{BASE_URL}/plugin.php?id=jnbux'
    try: r = session.get(bux_url, headers=HEADERS, timeout=TIMEOUT)
    except: return False
    if '开始参与任务' in r.text:
        session.get(f'{BASE_URL}/plugin.php?id=jnbux:jnbux&do=join&formhash={formhash}', headers={**HEADERS, 'Referer': bux_url}, timeout=TIMEOUT)
        time.sleep(1); r = session.get(bux_url, headers=HEADERS, timeout=TIMEOUT)
        print('[✓] 已加入Bux')
    tasks = re.findall(r'<a[^>]*href="javascript:;"\s*onclick="([^"]*)"[^>]*>\s*参与任务\s*</a>', r.text)
    if not tasks: print('[✓] 所有任务已完成'); return True
    print(f'[*] 发现 {len(tasks)} 个任务')
    ok = 0
    for idx, onclick in enumerate(tasks, 1):
        print(f'  -- 任务 {idx}/{len(tasks)} --')
        m = re.search(r'(openNewWindow[^(]+)\(\)', onclick)
        if not m: continue
        fn = re.escape(m.group(1))
        ad_url = None
        for pat in [rf'function\s+{fn}\s*\(\s*\)\s*{{[^}}]*window\.open\("([^"]+)"', rf'function\s+{fn}\s*\(\)[\s\S]*?window\.open\("([^"]+)"']:
            am = re.search(pat, r.text)
            if am: ad_url = urljoin(BASE_URL + '/', am.group(1)); break
        if not ad_url: continue
        try: session.get(ad_url, headers={**HEADERS, 'Referer': bux_url}, timeout=TIMEOUT, allow_redirects=True); time.sleep(3)
        except: pass
        ckm = re.search(r"showWindow\('check',\s*'([^']+)'\)", onclick)
        if ckm:
            ck = session.get(urljoin(BASE_URL + '/', ckm.group(1)), headers={**HEADERS, 'Referer': ad_url or bux_url}, timeout=TIMEOUT)
            if '检查成功' in ck.text or '积分已经加入' in ck.text: print(f'  [✓] 任务 {idx} 成功'); ok += 1
        time.sleep(2)
    print(f'[✓] 任务完成: {ok}/{len(tasks)}')
    return True

def main():
    cs = os.environ.get('ZODGAME_COOKIE', '').strip()
    if not cs: print('[✗] 未设置 ZODGAME_COOKIE'); sys.exit(1)
    s = requests.Session(); s.cookies.update(parse_cookie(cs))
    print('='*40+'\n  ZodGame 自动签到\n'+'='*40)
    fh = get_formhash(s)
    if not fh: print('[✗] Cookie过期'); sys.exit(1)
    print(f'formhash: {fh}')
    print('\n[*] 签到...'); sign_in(s, fh)
    print('\n[*] 广告任务...'); do_tasks(s, fh)
    print('\n[✓] 完成！')

if __name__ == '__main__': main()
