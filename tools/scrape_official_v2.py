import json,re,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'cards.json'
SETS=['OP01','OP02','OP03','OP04','OP05','OP06','OP07','OP08','OP09','OP10','OP11','OP12','OP13','OP14','OP15','OP16','OP17','EB01','EB02','EB03','EB04','PRB01','PRB02']
all_data={x:[] for x in SETS}; seen=set()
def walk(x):
 if isinstance(x,dict):
  raw=json.dumps(x,ensure_ascii=False)
  urls=re.findall(r'https?://[^\"\'\\ ]+',raw)
  image=next((u for u in urls if re.search(r'\.(?:jpg|jpeg|png|webp)',u,re.I)),None)
  text=' '.join(str(v) for v in x.values() if isinstance(v,(str,int,float)))
  m=re.search(r'((?:OP|EB|PRB)[-_ ]?\d{2}[-_ ]?\d{3}[A-Z]?)',text,re.I)
  if image and m:
   cid=m.group(1).upper().replace(' ','-').replace('_','-'); sid=next((s for s in SETS if cid.startswith(s+'-')),None)
   if sid and cid not in seen:
    name=next((str(v) for k,v in x.items() if k.lower() in ('name','cardname','card_name','title','cardtitle')), '')
    seen.add(cid); all_data[sid].append({'id':cid,'name':name,'image':image})
  for v in x.values(): walk(v)
 elif isinstance(x,list):
  for v in x: walk(v)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True); page=browser.new_page()
 def on_response(r):
  try:
   ct=r.headers.get('content-type',''); u=r.url.lower()
   if 'json' in ct or any(k in u for k in ('api','cardlist','card-list','weblist','windoent')): walk(r.json())
  except Exception: pass
 page.on('response',on_response); page.goto('https://www.onepiece-cardgame.cn/cardlist',wait_until='networkidle',timeout=90000)
 for _ in range(10): page.mouse.wheel(0,1800); page.wait_for_timeout(600)
 browser.close()
for v in all_data.values(): v.sort(key=lambda x:x['id'])
OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(all_data,ensure_ascii=False,indent=2),encoding='utf-8')
print('TOTAL',sum(len(v) for v in all_data.values())); [print(k,len(v)) for k,v in all_data.items()]