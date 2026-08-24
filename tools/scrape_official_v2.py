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

CARD_RE = re.compile(r'\b((?:OPC|EBC|PRBC)[-_ ]?\d{2}[-_ ]?\d{3}[A-Z]?|(?:OP|EB|PRB)[-_ ]?\d{2}[-_ ]?\d{3}[A-Z]?)\b', re.I)
SET_RE = re.compile(r'(?i)(OPC|EBC|PRBC|OP|EB|PRB)[-_ ]?(\d{2})')
IMG_RE = re.compile(r'\.(?:jpg|jpeg|png|webp)(?:[?#].*)?$', re.I)

def normalize_id(value):
    m = CARD_RE.search(str(value or ''))
    if not m:
        return None
    raw = re.sub(r'-+', '-', m.group(1).upper().replace('_','-').replace(' ','-'))
    return raw.replace('OPC-', 'OP').replace('EBC-', 'EB').replace('PRBC-', 'PRB')

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
        vals = list(obj.values())
        strings = [v for v in vals if isinstance(v, (str,int,float))]
        cid = next((normalize_id(v) for v in strings if normalize_id(v)), None)
        image = next((str(v) for v in strings if str(v).startswith(('http://','https://')) and IMG_RE.search(str(v))), None)
        if cid and image:
            name = next((v for k,v in obj.items() if str(k).lower() in {'name','cardname','card_name','title','cardtitle','cardnamecn','card_name_cn','cardnamezh','card_name_zh'}), '')
            add_card(cid, name, image)
        for v in vals:
            inspect_json(v)
    elif isinstance(obj, list):
        for v in obj:
            inspect_json(v)

def discover_set_urls(page):
    found = {}
    links = page.locator('a')
    for i in range(links.count()):
        try:
            a = links.nth(i)
            href = a.get_attribute('href') or ''
            text = a.inner_text(timeout=300)
            m = SET_RE.search(f'{href} {text}')
            if not m:
                continue
            prefix, num = m.group(1).upper(), m.group(2)
            sid = f'OP{num}' if prefix == 'OPC' else f'EB{num}' if prefix == 'EBC' else f'PRB{num}' if prefix == 'PRBC' else f'{prefix}{num}'
            if sid in SETS and href:
                found[sid] = urljoin(page.url, href)
        except Exception:
            pass
    return found

def scan_rendered_cards(page):
    imgs = page.locator('img')
    for i in range(imgs.count()):
        el = imgs.nth(i)
        try:
            src = el.get_attribute('src') or el.get_attribute('data-src') or el.get_attribute('data-original')
            if not src:
                continue
            src = urljoin(page.url, src)
            if not IMG_RE.search(src):
                continue
            parts = [el.get_attribute('alt') or '']
            for level in range(1, 6):
                try:
                    parts.append(el.locator('xpath=' + '/..' * level).inner_text(timeout=500))
                except Exception:
                    pass
            text = '\n'.join(parts)
            cid = normalize_id(text)
            if cid:
                name = re.sub(re.escape(cid), '', text, flags=re.I).strip(' |｜-\n\t')[:200]
                add_card(cid, name, src)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000}, locale='zh-CN')
    page = context.new_page()

    def on_response(r):
        responses.append({'url': r.url, 'status': r.status, 'content_type': r.headers.get('content-type','')})
        try:
            if 'json' in r.headers.get('content-type','').lower():
                inspect_json(r.json())
        except Exception:
            pass

    page.on('response', on_response)
    page.goto('https://www.onepiece-cardgame.cn/cardlist', wait_until='domcontentloaded', timeout=120000)
    page.wait_for_timeout(6000)
    set_urls = discover_set_urls(page)
    print('DISCOVERED SET URLS:', json.dumps(set_urls, ensure_ascii=False, indent=2))

    # Scan every official filter URL discovered from the site's own DOM.
    for sid in SETS:
        url = set_urls.get(sid)
        if not url:
            print(f'{sid}: filter URL not discovered')
            continue
        try:
            print(f'--- SCANNING {sid}: {url}')
            page.goto(url, wait_until='domcontentloaded', timeout=120000)
            page.wait_for_timeout(3500)
            for _ in range(30):
                page.mouse.wheel(0, 1600)
                page.wait_for_timeout(250)
            scan_rendered_cards(page)
            print(f'{sid}: {len(all_data[sid])} cards so far')
        except Exception as e:
            print(f'{sid}: ERROR {type(e).__name__}: {e}')

    DEBUG.mkdir(exist_ok=True)
    (DEBUG/'page-final.html').write_text(page.content(), encoding='utf-8')
    page.screenshot(path=str(DEBUG/'page-final.png'), full_page=False)
    (DEBUG/'network.json').write_text(json.dumps(responses, ensure_ascii=False, indent=2), encoding='utf-8')
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
