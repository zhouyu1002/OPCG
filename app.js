// 卡片資料集中在這裡，之後只要補充 image 欄位即可擴充。
const sets = [
  { id: 'OP01', name: 'OP01 佐羅十郎登場', cards: [] },
  { id: 'OP02', name: 'OP02 頂上決戰', cards: [] },
  { id: 'OP03', name: 'OP03 王國的傳奇', cards: [] },
  { id: 'OP04', name: 'OP04 謀略的王國', cards: [] },
  { id: 'OP05', name: 'OP05 新時代的主角們', cards: [] },
  { id: 'OP06', name: 'OP06 雙璧的覇者', cards: [] },
  { id: 'OP07', name: 'OP07 500年後的未來', cards: [] },
  { id: 'OP08', name: 'OP08 二人の覺醒', cards: [] },
  { id: 'OP09', name: 'OP09 新たなる皇帝', cards: [] },
  { id: 'OP10', name: 'OP10 王族の血統', cards: [] },
  { id: 'OP11', name: 'OP11 神速の拳', cards: [] },
  { id: 'OP12', name: 'OP12 Legacy of the Master', cards: [] },
  { id: 'OP13', name: 'OP13 Carrying on His Will', cards: [] },
  { id: 'OP14', name: 'OP14 予定追加', cards: [] },
  { id: 'OP15', name: 'OP15 予定追加', cards: [] },
];

const setButtons = document.querySelector('#setButtons');
const cardsGrid = document.querySelector('#cardsGrid');
const emptyState = document.querySelector('#emptyState');
const setName = document.querySelector('#setName');
const cardCount = document.querySelector('#cardCount');
const lightbox = document.querySelector('#lightbox');
const lightboxImage = document.querySelector('#lightboxImage');
const lightboxLabel = document.querySelector('#lightboxLabel');

function renderSetButtons() {
  setButtons.innerHTML = '';
  sets.forEach(set => {
    const button = document.createElement('button');
    button.className = 'set-button';
    button.textContent = set.id;
    button.title = set.name;
    button.addEventListener('click', () => selectSet(set.id, button));
    setButtons.appendChild(button);
  });
}

function selectSet(id, button) {
  document.querySelectorAll('.set-button').forEach(b => b.classList.remove('active'));
  button.classList.add('active');
  const set = sets.find(s => s.id === id);
  setName.textContent = `${set.id}｜${set.name}`;
  cardCount.textContent = `${set.cards.length} 張`;
  renderCards(set);
}

function renderCards(set) {
  emptyState.hidden = true;
  cardsGrid.hidden = false;
  cardsGrid.innerHTML = '';

  if (!set.cards.length) {
    cardsGrid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><h2>${set.id} 尚未加入卡圖</h2><p>請把卡片圖片放到 images/${set.id}/，並在 app.js 的 cards 陣列加入資料。</p></div>`;
    return;
  }

  set.cards.forEach(card => {
    const figure = document.createElement('figure');
    figure.className = 'card';
    figure.innerHTML = `<img src="${card.image}" alt="${card.id}" loading="lazy"><figcaption>${card.id}${card.name ? `｜${card.name}` : ''}</figcaption>`;
    figure.addEventListener('click', () => openLightbox(card));
    cardsGrid.appendChild(figure);
  });
}

function openLightbox(card) {
  lightboxImage.src = card.image;
  lightboxImage.alt = card.id;
  lightboxLabel.textContent = card.name ? `${card.id}｜${card.name}` : card.id;
  lightbox.hidden = false;
}

function closeLightbox() { lightbox.hidden = true; }
document.querySelector('#closeLightbox').addEventListener('click', closeLightbox);
lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
document.querySelector('#topButton').addEventListener('click', () => window.scrollTo({top:0,behavior:'smooth'}));

renderSetButtons();
