import json, re, sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE='https://www.onepiece-cardgame.cn'
CARDLIST=BASE+'/cardlist'
OUT=Path(__file__).resolve().parents[1]/'data'/'api-discovery.json'

s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36','Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8'})
r=s.get(CARDLIST,timeout=30); r.raise_for_status()
html=r.text
soup=BeautifulSoup(html,'html.parser')
scripts=[urljoin(BASE,x.get('src')) for x in soup.find_all('script',src=True)]
patterns=[r'https?://[^\"\']+',r'[^\"\']*(?:api|cardList|cardlist|card-list|weblist)[^\"\']*']
found=set()
for src in scripts:
    try:
        text=s.get(src,timeout=20).text
    except Exception: continue
    for p in patterns:
        for x in re.findall(p,text,re.I):
            if 'card' in x.lower() or 'api' in x.lower() or 'windoent' in x.lower(): found.add(x)
for x in re.findall(r'https?://[^\"\'\s<>]+',html):
    if 'card' in x.lower() or 'api' in x.lower() or 'windoent' in x.lower(): found.add(x)
result={'cardlist':CARDLIST,'scripts':scripts,'candidates':sorted(found)}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
