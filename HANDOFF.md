# 專案交接：美化版基板庫存管理系統網頁

> ⚠️ 此 repo 為 Public，本檔不放明文密碼等機敏資訊。

## 一句話
把舊的「基板庫存管理系統」重製成手機優先、iOS 液態玻璃風格的單頁網頁，
串接 Google Sheet 即時資料，已部署到 GitHub Pages。

## 檔案位置（本機 macOS）
- 專案資料夾：`/Users/tom464072/Library/CloudStorage/OneDrive-HOYACorporation/claude_code_project/美化版_庫存管理系統網頁`
- 主要檔案：
  - `index.html`（單一檔案 App，HTML+CSS+JS 全包）
  - `data.js`（靜態快照，即時讀取失敗時的後備，`window.INVENTORY_DATA`）
  - `manifest.webmanifest`（PWA / 桌面 icon 設定）
  - `assets/icon.svg` + `assets/icon-{16,32,180,192,512}.png`（墨綠立體庫存箱 icon）
- 舊版（未動，勿覆蓋）：同層的 `庫存管理系統網頁/`（另一個 repo `substrate-inventory`）

## 部署
- GitHub repo：`https://github.com/redarmychenzz/substrate-inventory-v2`（Public）
- 線上網址：`https://redarmychenzz.github.io/substrate-inventory-v2/`
- Pages 設定：main 分支 / root
- 更新流程：改 `index.html` → 在專案資料夾 `git add -A && git commit && git push origin main` → Pages 自動重建（約 1–2 分鐘，手機需強制重新整理清快取）
- git 作者用 `redarmychenzz / redarmychenzz@gmail.com`；commit 訊息尾端加
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- 沒裝 `gh` CLI；git https 認證已通

## 密碼鎖
- 密碼：**不列於此公開檔**（owner 已知；SHA-256 hash 已寫在 `index.html` 的 `PWD_HASH`）
- localStorage key：`inv_auth`

## 即時資料（Google Sheet，JSONP gviz，支援 file:// 與 https://）
- Sheet ID / gid 皆已寫在 `index.html`（`SHEET_ID` / `BLANKS_GID` / `G6012_GID`）
- 基板現況分頁 gid=`0`；6012 使用紀錄分頁 gid=`57603327`
- Sheet 必須維持「知道連結的人可檢視」
- 行為：先用 `data.js` 靜態秒開 → 背景 JSONP 抓即時覆蓋 → 失敗回退靜態
- 欄位靠名稱對應（`findCol`），Sheet 欄序調動不會壞

## 技術/架構重點
- 純靜態、無 build、vanilla JS
- 主題：淺/深色手動切換（localStorage `inv_theme`），CSS 變數
- 版面：手機優先；≥900px 為電腦版（左側欄取代底部 dock）
- 核心函式：`build(D)=buildBlanks(D)+build6012(D)`、`mapBlanks/map6012`、`loadLive()`（重新整理鈕共用）、`switchPage(p)`、`collapseAll()`、`toggleSize/toggleRec`

## 已完成功能
### 分頁1「Team1 基板 list」
- Hero：icon+標題+最後更新時間+重新整理鈕+主題鈕；「基板數量」大數字(pcs) + A倉(藍)/B倉(綠) 藥丸
- 尺寸清單：手風琴（一次只展開一個），左側 icon + 尺寸(數字不重疊) + A/B/共 徽章
- 展開內容：批號可左右滑卡片（電腦版有左右箭頭+圓點）；費用化只有 ✘ 顯示紅「未費用」
### 分頁2「6012 使用紀錄」
- Hero：未使用庫存 / 可報廢（pcs）
- 近 7 天展開、其餘收在「顯示更早的紀錄」（基準=最新一筆紀錄往回 7 天）
- 排除方式=「購入」的紀錄
- 紀錄卡手風琴（一次只展開一個）；收合標題= 機台徽章 + PM項目 + 方式徽章
- 標題文字 fallback：PM項目 → 描畫Pattern → 備註 → 方式
- 機台配色：TI藍/TC綠/TK琥珀/其他紫；方式：報廢紅/留存藍
- 「收起更早的紀錄」按鈕展開後變縮窄實心藍，區別於半透明資料卡
### 共用
- 底部液態玻璃 dock（手機）/ 左側欄（電腦）切兩頁，狀態同步
- 左右滑動切換分頁（基板左滑→6012、6012右滑→基板；避開輪播與垂直捲動、鎖定時不觸發）
- 桌面/網頁 icon（墨綠底立體紙箱+勾選徽章）、PWA manifest、iOS 全螢幕 meta

## 待確認 / 注意
- iOS 上下白邊：已用標準修法（html 純色 background-color `--bg-solid` + `apple-mobile-web-app-status-bar-style: black-translucent` + 動態 theme-color），但需在真 iPhone 確認；換新 icon/全螢幕需「重新加入主畫面」
- 測試提醒：自動化預覽分頁常是 hidden，會凍結 requestAnimationFrame 與 CSS transition，導致展開動畫/寬度變化在截圖看不到終態（真機正常）。驗證時可暫時注入 `*{transition:none!important;animation:none!important}` 或直接設終態
- 展開動畫參考 finance-dashboard：`.detail{height:0→scrollHeight}` + `cubic-bezier(0.22,1,0.36,1)` + 內容用 `setTimeout`（勿用 rAF）stagger 淡入
