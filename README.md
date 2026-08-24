# OPCG 簡中版卡片圖鑑

目前已建立純前端卡片圖鑑頁面：

- OP01～OP15 彈數按鈕
- 點選彈數後，一頁顯示該彈全部卡片
- 卡片圖片採響應式網格排列
- 點擊卡片可放大查看
- 手機與電腦版自適應

## 卡片圖片格式

建議將圖片放在：

```text
images/
├─ OP01/
│  ├─ OP01-001.jpg
│  ├─ OP01-002.jpg
│  └─ ...
├─ OP02/
│  ├─ OP02-001.jpg
│  └─ ...
```

然後在 `app.js` 對應的 `cards` 陣列加入圖片路徑，例如：

```js
cards: [
  { id: 'OP01-001', image: 'images/OP01/OP01-001.jpg' },
  { id: 'OP01-002', image: 'images/OP01/OP01-002.jpg' }
]
```

## GitHub Pages

Repository → **Settings → Pages** → Source 選 **Deploy from a branch** → Branch 選 `main` / `/ (root)` → Save。

之後即可使用 GitHub Pages 開啟網站。
