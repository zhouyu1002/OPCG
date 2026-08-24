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

CARD_RE = re.compile(r'\b((?:OPC|EBC|PRBC|OP|EB|PRB)[-_ ]?\d{2}[-_ ]?\d{3}[A-Z]?)\b', re.I)
SET_CODE_RE = re.compile(r'(?i)(OPC|EBC|PRBC|OP|EB|PRB)[-_ ]?(\d{2})')
IMG_RE = re.compile(r'\.(?:jpg|jpeg|png|webp)(?:[?#].*)?$', re.I)

API_BASE = 'https://webadmin.windoent.com/front/op-public'
OFFERING_API = f'{API_BASE}/cardType/cardofferingtype/cachelist'
CARD_API = f'{API_BASE}/cardList/cardlist/weblist'


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
    """Recursively find card id + image pairs in arbitrary API JSON."""
    if isinstance(obj, dict):
        vals = list(obj.values())
        strings = [v for v in vals if isinstance(v, (str, int, float))]
        cid = next((normalize_id(v) for v in strings if normalize_id(v)), None)
        image = next((str(v) for v in strings if str(v).startswith(('http://','https://')) and IMG_RE.search(str(v))), None)
        if cid and image:
            name = next((v for k,v in obj.items() if str(k).lower() in {
                'name','cardname','card_name','title','cardtitle','cardnamecn',
                'card_name_cn','cardnamezh','card_name_zh','cnname','chinesename'
            }), '')
            add_card(cid, name, image)
        for v in vals:
            inspect_json(v)
    elif isinstance(obj, list):
        for v in obj:
            inspect_json(v)


def extract_set_names(obj):
    """Find official offering names such as 补充包 ...【OP-17】 from cachelist JSON."""
    found = {}
    if isinstance(obj, dict):
        for v in obj.values():
            for sid, text in extract_set_names(v).items():
                found[sid] = text
    elif isinstance(obj, list):
        for v in obj:
            for sid, text in extract_set_names(v).items():
                found[sid] = text
    elif isinstance(obj, str):
        m = re.search(r'(?i)(OPC|EBC|PRBC|OP|EB|PRB)[-_ ]?(\d{2})', obj)
        if m:
            prefix, num = m.group(1).upper(), m.group(2)
            sid = f'OP{num}' if prefix in ('OP','OPC') else f'EB{num}' if prefix in ('EB','EBC') else f'PRB{num}'
            if sid in SETS and '【' in obj and '】' in obj:
                found[sid] = obj
    return found


def extract_text_set_names(html):
    found = {}
    # Fallback: the offering dropdown is rendered in the HTML even when it is not an <a> link.
    for m in re.finditer(r'([^<>]{0,160}【((?:OPC|EBC|PRBC|OP|EB|PRB)-\d{2})】)', html, re.I):
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        code = m.group(2).upper().replace('OPC-', 'OP').replace('EBC-', 'EB').replace('PRBC-', 'PRB')
        if code in SETS:
            found[code] = text + '【' + m.group(2).upper() + '】'
    return found


def api_json(request, url, params=None):
    resp = request.get(url, params=params or {}, timeout=120000)
    responses.append({'url': resp.url, 'status': resp.status, 'content_type': resp.headers.get('content-type','')})
    if not resp.ok:
        raise RuntimeError(f'HTTP {resp.status}: {resp.url}')
    return resp.json()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000}, locale='zh-CN')
    page = context.new_page()
    request = context.request

    # Open the official site first so the same public origin/session is used.
    page.goto('https://www.onepiece-cardgame.cn/cardlist', wait_until='domcontentloaded', timeout=120000)
    page.wait_for_timeout(4000)

    print('===== DISCOVER OFFICIAL CARD OFFERINGS =====')
    offering_names = {}
    try:
        offering_json = api_json(request, OFFERING_API)
        offering_names.update(extract_set_names(offering_json))
        print('API offerings:', json.dumps(offering_names, ensure_ascii=False, indent=2))
    except Exception as e:
        print('Offering API failed:', type(e).__name__, e)

    # Also inspect rendered HTML for any offering names not present in the API payload.
    offering_names.update(extract_text_set_names(page.content()))
    print('FINAL OFFERINGS:', json.dumps(offering_names, ensure_ascii=False, indent=2))

    # The official card-list API is paginated. Query every requested set independently.
    for sid in SETS:
        offer = offering_names.get(sid)
        if not offer:
            print(f'{sid}: official offering name not discovered')
            continue

        print(f'--- API SCANNING {sid}: {offer} ---')
        before = len(all_data[sid])
        try:
            # Use a deliberately large page size and continue until an empty page.
            # This avoids depending on the website's current UI pagination.
            for page_no in range(1, 101):
                payload = api_json(request, CARD_API, {
                    'cardOfferType': offer,
                    'cardColor': '',
                    'cardType': '',
                    'cardCartograph': '',
                    'subscript': '',
                    'limit': 100,
                    'page': page_no,
                })
                before_page = len(all_data[sid])
                inspect_json(payload)
                added = len(all_data[sid]) - before_page
                print(f'{sid} page {page_no}: +{added}, total {len(all_data[sid])}')
                # Once a page contributes no new cards, the API has reached its end.
                if added == 0:
                    break
        except Exception as e:
            print(f'{sid}: API ERROR {type(e).__name__}: {e}')

        # Fallback for a set where the API returned no card pairs: scan the rendered page.
        if len(all_data[sid]) == before:
            try:
                url = 'https://www.onepiece-cardgame.cn/cardlist'
                page.goto(url, wait_until='domcontentloaded', timeout=120000)
                page.wait_for_timeout(3000)
            except Exception:
                pass
        print(f'{sid}: {len(all_data[sid])} cards total')

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
