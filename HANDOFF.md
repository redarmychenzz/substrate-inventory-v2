# 專案交接：美化版基板庫存管理系統網頁

> ⚠️ 此 repo 為 Public，本檔不放明文密碼等機敏資訊。

## 一句話
把舊的「基板庫存管理系統」重製成手機優先、iOS 液態玻璃風格的單頁網頁，
串接 Google Sheet 即時資料，已部署到 GitHub Pages。

## 檔案位置（本機 macOS）
- 專案資料夾：`~/Library/CloudStorage/OneDrive-HOYACorporation/claude_code_project/美化版_庫存管理系統網頁`
  （OneDrive 同步，曾出現在 `/Users/tom464072/` 與 `/Users/tom/` 兩台機器；跨機同步會改檔案權限，repo 已設 `core.fileMode false` 忽略）
- 主要檔案：
  - `index.html`（單一檔案 App，HTML+CSS+JS 全包）
  - `data.js`（靜態快照，即時讀取失敗時的後備，`window.INVENTORY_DATA`；由 Actions 自動更新）
  - `scripts/update_data.py`（快照更新腳本，GitHub Actions 定時執行）
  - `.github/workflows/update-data.yml`（每 30 分鐘排程；改此檔需在 GitHub 網頁編輯）
  - `manifest.webmanifest`（PWA / 桌面 icon 設定）
  - `assets/icon.svg` + `assets/icon-{16,32,180,192,512}.png`（墨綠立體庫存箱 icon）
- 舊版（未動，勿覆蓋）：同層的 `庫存管理系統網頁/`（另一個 repo `substrate-inventory`）

## 部署
- GitHub repo：`https://github.com/redarmychenzz/substrate-inventory-v2`（Public）
- 線上網址：`https://redarmychenzz.github.io/substrate-inventory-v2/`
- Pages 設定：main 分支 / root
- 更新流程：改 `index.html` → 在專案資料夾 `git add -A && git commit && git push origin main` → Pages 自動重建（約 1–2 分鐘，手機需強制重新整理清快取）
- git 作者用 `redarmychenzz / redarmychenzz@gmail.com`；commit 訊息尾端加
  `Co-Authored-By: <當前 Claude 模型名> <noreply@anthropic.com>`（近期為 Claude Fable 5）
- 沒裝 `gh` CLI；git https 認證已通（PAT 無 `workflow` scope，推不動 `.github/workflows/`）
- Actions 會自動 commit 快照，本機推送前建議先 `git pull --rebase origin main`

## 密碼鎖
- 密碼：**不列於此公開檔**（owner 已知；SHA-256 hash 已寫在 `index.html` 的 `PWD_HASH`）
- localStorage key：`inv_auth`

## 即時資料（Google Sheet，JSONP gviz，支援 file:// 與 https://）
- Sheet ID / gid 皆已寫在 `index.html`（`SHEET_ID` / `BLANKS_GID` / `G6012_GID`）
- 基板現況分頁 gid=`0`；6012 使用紀錄分頁 gid=`57603327`
- Sheet 必須維持「知道連結的人可檢視」
- 行為：先用 `data.js` 靜態秒開 → 背景 JSONP 抓即時覆蓋 → 失敗回退靜態
- 欄位靠名稱對應（`findCol`），Sheet 欄序調動不會壞
- 快照自動更新（因公司網路擋 docs.google.com，回退時資料不能太舊）：
  - GitHub Actions（`.github/workflows/update-data.yml`）每 30 分鐘跑 `scripts/update_data.py`
  - 腳本抓 gviz 重建 `data.js`（欄位對應邏輯與 index.html 一致）；
    只在資料有變化、或快照逾 24h（心跳）時 commit，避免噪音
  - 注意：本機 PAT 無 `workflow` scope，改 workflow 檔要在 GitHub 網頁上編輯

## 技術/架構重點
- 純靜態、無 build、vanilla JS
- 主題：淺/深色手動切換（localStorage `inv_theme`），CSS 變數
- 版面：手機優先；≥900px 為電腦版（左側欄取代底部 dock、頁寬 800px、字級放大）
- 核心函式：`build(D)=buildBlanks(D)+build6012(D)`、`mapBlanks/map6012`、`loadLive()`（重新整理鈕共用）、`switchPage(p)`、`collapseAll()`、`toggleSize/toggleRec`、`deskList/deskRow`（電腦版條列式）、`useTag`（用途徽章）

## 已完成功能
### 分頁1「Team1 基板 list」
- Hero：icon+標題+最後更新時間+重新整理鈕+主題鈕；「基板數量」大數字(pcs) + A倉(藍)/B倉(綠) 藥丸
- 尺寸清單：手風琴（一次只展開一個），左側 icon + 尺寸(數字不重疊) + A/B/共 徽章
- 篩選列（僅手機 <900px；電腦版 CSS 隱藏）：倉別（全部/A倉/B倉）＋載具（全部＋依資料動態產生，如 Case/台車）
  - 狀態存 `fWh`/`fCar`（記憶體，不落地）；點選即重建清單，徽章數重算、無符合顯示空狀態
  - Hero 大數字維持全量不受篩選影響；即時更新後篩選保留（選項消失則自動回「全部」）
  - 視窗跨到 ≥900px 時自動重置篩選（matchMedia change），避免電腦版看不到篩選列卻被篩選
- 展開內容（手機 <900px）：批號左右滑卡片＋圓點；欄位含品號（`pn`，Sheet「品號」欄）；費用化只有 ✘ 顯示紅「未費用」
- 展開內容（電腦 ≥900px）：條列式（帳冊表格＋分倉分組 `.desk-list`）——A倉/B倉 分組、左側色條生長動畫、列 stagger 浮現、hover 淡藍高亮；載具/屬性欄置中；第一欄=批號/規格/品號；取代輪播（箭頭已移除）
- 電腦版展開時點欄塊外空白處即收合（document click 監聽，排除 .size-item/.hero/.sidebar/.dock-wrap/.lock）
- 批號卡/條列皆有「屬性」徽章（Sheet L 欄「用途」，載具旁）：工程藍 / 調查琥珀 / 校正青 / 回收綠 / 其他灰（`useTag`；`data.js` 快照含 `use` 欄位）
### 分頁2「6012 使用紀錄」
- Hero：未使用庫存 / 可報廢（pcs）
- 近 7 天展開、其餘收在「顯示更早的紀錄」（基準=最新一筆紀錄往回 7 天）
- 排除方式=「購入」的紀錄
- 紀錄卡手風琴（一次只展開一個）；收合標題= 機台徽章 + PM項目 + 方式徽章
- 標題文字 fallback：PM項目 → 描畫Pattern → 備註 → 方式
- 機台配色：TI藍/TC綠/TK琥珀/其他紫；方式：報廢紅/留存藍
- 「收起更早的紀錄」按鈕展開後變縮窄實心藍，區別於半透明資料卡
### 共用
- 動畫系統（全部只動 transform/opacity；`prefers-reduced-motion` 時全關）：
  - 背景呼吸光暈 `.bg-fx`（3 顆色暈 16/20/24s 漂移，深色模式降透明度）
  - 卡片 hover 懸浮＋光澤掃過＋icon 擺動（`@media (hover:hover)` 限滑鼠裝置）
  - Hero 數字滾動 `setNum()`（setTimeout 驅動，勿改回 rAF）＋倉別藥丸彈入 `popPills()`
  - 列按壓微縮（:active）、展開箭頭回彈（--spring）
  - 分頁切換帶方向滑動（switchPage 設 `--pg-dx`）
  - 重新整理鈕：轉圈→綠勾＋漣漪（成功）/紅驚嘆號（失敗）`refreshFeedback()`
- 底部液態玻璃 dock（手機）/ 左側欄（電腦）切兩頁，狀態同步
- 左右滑動切換分頁（基板左滑→6012、6012右滑→基板；避開輪播與垂直捲動、鎖定時不觸發）
- 桌面/網頁 icon（墨綠底立體紙箱+勾選徽章）、PWA manifest、iOS 全螢幕 meta

## 進度紀錄
### 2026/07/16–17
- 屬性徽章（Sheet「用途」欄）：工程/調查/校正/回收/其他，手機卡片與電腦條列皆顯示（a6ca048）
- 電腦版展開改條列式：帳冊表格＋分倉分組，取代輪播（a6ca048）
- 載具/屬性欄置中、「用途」表頭改「屬性」、電腦版頁寬 600→800px＋字級放大（5bcfdc3）
- 全站動畫系統六件套：背景光暈/卡片懸浮光澤/數字滾動/微互動/分頁過場/重新整理回饋（b6dda1e）
- 基板加品號（pn）；電腦版點欄塊外空白處收合（d582056）；品號去除前綴字樣（551e100）
- 解決公司網路擋 Google Sheet：GitHub Actions 每 30 分鐘自動更新 data.js 快照
  （scripts/update_data.py + update-data.yml，資料變更或逾 24h 心跳才 commit）
### 2026/08/06
- 基板 list 新增倉別/載具篩選列（53e10b2）
- 篩選列改為僅手機版顯示，電腦版隱藏；跨到電腦版寬度自動重置篩選（e04ae99）

## 待確認 / 注意
- iOS 上下白邊：已用標準修法（html 純色 background-color `--bg-solid` + `apple-mobile-web-app-status-bar-style: black-translucent` + 動態 theme-color），但需在真 iPhone 確認；換新 icon/全螢幕需「重新加入主畫面」
- 測試提醒：自動化預覽分頁常是 hidden，會凍結 requestAnimationFrame 與 CSS transition，導致展開動畫/寬度變化在截圖看不到終態（真機正常）。驗證時可暫時注入 `*{transition:none!important;animation:none!important}` 或直接設終態
- 展開動畫參考 finance-dashboard：`.detail{height:0→scrollHeight}` + `cubic-bezier(0.22,1,0.36,1)` + 內容用 `setTimeout`（勿用 rAF）stagger 淡入
