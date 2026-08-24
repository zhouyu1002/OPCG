import json
import re
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'cards.json'
DEBUG = ROOT / 'debug'
SETS = [f'OP{i:02d}' for i in range(1, 18)] + ['EB01','EB02','EB03','EB04','PRB01','PRB02']
all_data = {s: [] for s in SETS}
seen = set()
responses = []

CARD_RE = re.compile(r'\b((?:OP|EB|PRB)[-_ ]?\d{2}[-_ ]?\d{3}[A-Z]?)\b', re.I)
IMG_RE = re.compile(r'\.(?:jpg|jpeg|png|webp)(?:[?#].*)?$', re.I)

def normalize_id(value):
    m = CARD_RE.search(str(value or ''))
    if not m:
        return None
    return m.group(1).upper().replace('_','-').replace(' ','-')

def set_for(cid):
    return next((s for s in SETS if cid.startswith(s + '-')), None)

def add_card(cid, name, image):
    if not cid or not image:
        return
    sid = set_for(cid)
    if not sid or cid in seen:
        return
    seen.add(cid)
    all_data[sid].append({'id': cid, 'name': str(name or ''), 'image': image})

def inspect_json(obj):
    if isinstance(obj, dict):
        values = list(obj.values())
        strings = [v for v in values if isinstance(v, (str,int,float))]
        cid = None
        for v in strings:
            cid = normalize_id(v)
            if cid: break
        image = None
        for v in strings:
            sv = str(v)
            if sv.startswith(('http://','https://')) and IMG_RE.search(sv):
                image = sv
                break
        if cid and image:
            name = ''
            for k,v in obj.items():
                if str(k).lower() in {'name','cardname','card_name','title','cardtitle','cardnamecn','card_name_cn'}:
                    name = v; break
            add_card(cid, name, image)
        for v in values:
            inspect_json(v)
    elif isinstance(obj, list):
        for v in obj:
            inspect_json(v)

def save_debug(page):
    DEBUG.mkdir(exist_ok=True)
    (DEBUG/'page.html').write_text(page.content(), encoding='utf-8')
    page.screenshot(path=str(DEBUG/'page.png'), full_page=True)
    (DEBUG/'network.json').write_text(json.dumps(responses, ensure_ascii=False, indent=2), encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000}, locale='zh-CN')
    page = context.new_page()

    def on_response(r):
        info = {'url': r.url, 'status': r.status, 'content_type': r.headers.get('content-type','')}
        responses.append(info)
        try:
            ct = r.headers.get('content-type','').lower()
            if 'json' in ct:
                inspect_json(r.json())
        except Exception:
            pass

    page.on('response', on_response)
    page.goto('https://www.onepiece-cardgame.cn/cardlist', wait_until='domcontentloaded', timeout=120000)
    page.wait_for_timeout(5000)

    # Trigger lazy-loaded content and inspect the rendered DOM.
    for _ in range(20):
        page.mouse.wheel(0, 1800)
        page.wait_for_timeout(700)

    # Collect every rendered image and nearby text. This is intentionally broad
    # because the official site's frontend structure can change independently.
    imgs = page.locator('img')
    for i in range(imgs.count()):
        el = imgs.nth(i)
        try:
            src = el.get_attribute('src') or el.get_attribute('data-src') or el.get_attribute('data-original')
            if not src:
                continue
            src = urljoin(page.url, src)
            alt = el.get_attribute('alt') or ''
            parent_text = el.locator('xpath=..').inner_text(timeout=1000)
            text = f'{alt} {parent_text}'
            cid = normalize_id(text)
            if not cid:
                # Search a few ancestor levels for the card number.
                for level in range(2,5):
                    try:
                        t = el.locator('xpath=' + '/..'*level).inner_text(timeout=500)
                        cid = normalize_id(t)
                        if cid:
                            text = t
                            break
                    except Exception:
                        pass
            if cid and (src.startswith('http') or src.startswith('//')):
                name = text.replace(cid, '').strip(' |｜-\n\t')[:200]
                add_card(cid, name, src)
        except Exception:
            pass

    save_debug(page)
    browser.close()

for values in all_data.values():
    values.sort(key=lambda x: x['id'])
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding='utf-8')

print('===== OPCG SCRAPER DIAGNOSTIC =====')
print('TOTAL:', sum(len(v) for v in all_data.values()))
for s in SETS:
    print(f'{s}: {len(all_data[s])}')
print('NETWORK RESPONSES:', len(responses))
print('DEBUG FILES:', DEBUG)
if sum(len(v) for v in all_data.values()) == 0:
    print('WARNING: no cards detected; inspect debug/page.html, debug/page.png and debug/network.json')
