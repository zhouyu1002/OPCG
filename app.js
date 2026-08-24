const SETS = [
  {id:'OP01',code:'OPC-01',name:'冒险的黎明',type:'main'},{id:'OP02',code:'OPC-02',name:'顶尖决战',type:'main'},
  {id:'OP03',code:'OPC-03',name:'强大的敌人',type:'main'},{id:'OP04',code:'OPC-04',name:'诡计的王国',type:'main'},
  {id:'OP05',code:'OPC-05',name:'新时代的主角',type:'main'},{id:'OP06',code:'OPC-06',name:'双璧的霸者',type:'main'},
  {id:'OP07',code:'OPC-07',name:'500年后的未来',type:'main'},{id:'OP08',code:'OPC-08',name:'二人的觉醒',type:'main'},
  {id:'OP09',code:'OPC-09',name:'新帝降临',type:'main'},{id:'OP10',code:'OPC-10',name:'王族血统',type:'main'},
  {id:'OP11',code:'OPC-11',name:'神速之拳',type:'main'},{id:'OP12',code:'OPC-12',name:'师徒的情义',type:'main'},
  {id:'OP13',code:'OPC-13',name:'继承的意志',type:'main'},{id:'OP14',code:'OPC-14',name:'梦想的航海',type:'main'},
  {id:'OP15',code:'OPC-15',name:'神之岛的冒险',type:'main'},{id:'OP16',code:'OPC-16',name:'四皇海贼团',type:'main'},
  {id:'OP17',code:'OPC-17',name:'最强斗士',type:'main'},
  {id:'EB01',code:'EB-01',name:'Extra Booster 01',type:'special'},{id:'EB02',code:'EB-02',name:'Anime 25th Collection',type:'special'},
  {id:'EB03',code:'EB-03',name:'Extra Booster 03',type:'special'},{id:'EB04',code:'EB-04',name:'Extra Booster 04',type:'special'},
  {id:'PRB01',code:'PRB-01',name:'历代典藏合集',type:'special'}
];
const setButtons=document.querySelector('#setButtons'),cardsGrid=document.querySelector('#cardsGrid'),emptyState=document.querySelector('#emptyState'),setName=document.querySelector('#setName'),cardCount=document.querySelector('#cardCount'),lightbox=document.querySelector('#lightbox'),lightboxImage=document.querySelector('#lightboxImage'),lightboxLabel=document.querySelector('#lightboxLabel');
let cardData={};
async function loadCardData(){try{const r=await fetch(`data/cards.json?v=${Date.now()}`);if(!r.ok)throw Error(r.status);cardData=await r.json()}catch(e){console.warn('官方卡圖資料尚未抓取',e);cardData={}}}
function renderSetButtons(){setButtons.innerHTML='';let group='';SETS.forEach(s=>{if(s.type!==group){group=s.type;const t=document.createElement('div');t.className='set-group-title';t.textContent=s.type==='main'?'正式補充包':'特別／豪華補充包';setButtons.appendChild(t)}const b=document.createElement('button');b.className='set-button';b.textContent=s.id;b.title=`${s.code}｜${s.name}`;b.onclick=()=>selectSet(s.id,b);setButtons.appendChild(b)})}
function selectSet(id,b){document.querySelectorAll('.set-button').forEach(x=>x.classList.remove('active'));b.classList.add('active');const s=SETS.find(x=>x.id===id),cards=cardData[id]||[];setName.textContent=`${s.code}｜${s.name}`;cardCount.textContent=`${cards.length} 張`;renderCards(s,cards)}
function esc(v){return String(v??'').replace(/[&<>\'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','"':'&quot;'}[c]))}
function renderCards(s,cards){emptyState.hidden=true;cardsGrid.hidden=false;cardsGrid.innerHTML='';if(!cards.length){cardsGrid.innerHTML=`<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">📷</div><h2>${s.id} 尚未抓到官方卡圖</h2><p>官方卡表抓取完成後，重新整理即可看到卡片。</p></div>`;return}cards.forEach(c=>{const f=document.createElement('figure');f.className='card';f.innerHTML=`<img src="${esc(c.image)}" alt="${esc(c.id)}" loading="lazy"><figcaption>${esc(c.id)}${c.name?`｜${esc(c.name)}`:''}</figcaption>`;f.onclick=()=>openLightbox(c);cardsGrid.appendChild(f)})}
function openLightbox(c){lightboxImage.src=c.image;lightboxImage.alt=c.id;lightboxLabel.textContent=c.name?`${c.id}｜${c.name}`:c.id;lightbox.hidden=false}function closeLightbox(){lightbox.hidden=true}
document.querySelector('#closeLightbox').onclick=closeLightbox;lightbox.onclick=e=>{if(e.target===lightbox)closeLightbox()};document.onkeydown=e=>{if(e.key==='Escape')closeLightbox()};document.querySelector('#topButton').onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
(async()=>{renderSetButtons();await loadCardData()})();
