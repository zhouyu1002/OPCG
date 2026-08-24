import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

BASE='https://www.onepiece-cardgame.cn/cardlist'
OUT=Path('data/cards.json')
# 官方卡表使用动态 API；本程式透過瀏覽器攔截官方頁面實際請求，不猜測圖片網址。
SETS=['OP01','OP02','OP03','OP04','OP05','OP06','OP07','OP08','OP09','OP10','OP11','OP12','OP13','OP14','OP15','OP16','OP17','EB01','EB02','EB03','EB04','PRB01','PRB02']

CARD_RE=re.compile(r'\b((?:OP|EB|PRB|ST|P)-?\d{2,3})\b',re.I)
IMG_RE=re.compile(r'\.(?:jpg|jpeg|png|webp)(?:\?|$)',re.I)

def walk(obj, out):
    if isinstance(obj, dict):
        # 尋找一個物件中可能的卡號與圖片欄位
        text=' '.join(str(obj.get(k,'')) for k in ('cardNo','cardNumber','cardCode','number','code','id','name','title'))
        m=CARD_RE.search(text)
        image=None
        for k,v in obj.items():
            if isinstance(v,str) and IMG_RE.search(v) and ('http' in v):
                image=v; break
        if m and image:
            out.append({'id':m.group(1).upper().replace('OP-','OP').replace('EB-','EB').replace('PRB-','PRB'),'image':image,'name':str(obj.get('name') or obj.get('title') or '')})
        for v in obj.values(): walk(v,out)
    elif isinstance(obj,list):
        for v in obj: walk(v,out)

async def main():
    all_cards={s:[] for s in SETS}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()
        responses=[]
        page.on('response', lambda r: responses.append(r))
        await page.goto(BASE, wait_until='domcontentloaded', timeout=120000)
        await page.wait_for_timeout(10000)
        # 嘗試滾動觸發 lazy loading / infinite scroll
        for _ in range(12):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1000)
        for r in responses:
            ct=r.headers.get('content-type','')
            if 'json' not in ct: continue
            try:
                data=await r.json()
            except Exception: continue
            found=[]; walk(data,found)
            for c in found:
                sid=c['id'].split('-')[0]
                if sid in all_cards: all_cards[sid].append(c)
        await browser.close()
    # 去重、排序；若官方 API 沒有一次回傳全部資料，保留目前抓到的資料供後續擴充。
    for s in all_cards:
        uniq={c['id']+c['image']:c for c in all_cards[s]}
        all_cards[s]=sorted(uniq.values(),key=lambda x:x['id'])
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(all_cards,ensure_ascii=False,indent=2),encoding='utf-8')
    total=sum(map(len,all_cards.values()))
    print(f'完成：{total} 張卡片資料 -> {OUT}')
    for s in SETS:
        print(f'{s}: {len(all_cards[s])}')

if __name__=='__main__': asyncio.run(main())
