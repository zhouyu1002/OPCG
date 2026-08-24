import json
import hashlib
import mimetypes
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'cards.json'
IMG_ROOT = ROOT / 'images'

cards = json.loads(DATA.read_text(encoding='utf-8'))
count = 0
failed = []

for set_id, items in cards.items():
    out_dir = IMG_ROOT / set_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for card in items:
        cid = card.get('id')
        url = card.get('image')
        if not cid or not url:
            continue
        # Keep the original extension when available; PNG/JPG are both served fine by Pages.
        path_hint = url.split('?', 1)[0].split('#', 1)[0]
        ext = Path(path_hint).suffix.lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.webp'}:
            ext = '.png'
        out = out_dir / f'{cid}{ext}'
        try:
            if out.exists() and out.stat().st_size > 0:
                card['localImage'] = f'images/{set_id}/{out.name}'
                continue
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142 Safari/537.36',
                'Referer': 'https://www.onepiece-cardgame.cn/cardlist',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            })
            with urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) < 1000:
                raise RuntimeError(f'file too small: {len(data)} bytes')
            out.write_bytes(data)
            card['localImage'] = f'images/{set_id}/{out.name}'
            count += 1
        except Exception as e:
            failed.append({'id': cid, 'url': url, 'error': str(e)})

DATA.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'DOWNLOADED: {count}')
print(f'FAILED: {len(failed)}')
if failed:
    (ROOT / 'debug').mkdir(exist_ok=True)
    (ROOT / 'debug' / 'image-download-failures.json').write_text(json.dumps(failed, ensure_ascii=False, indent=2), encoding='utf-8')
    for x in failed[:20]:
        print('FAIL', x['id'], x['error'])
