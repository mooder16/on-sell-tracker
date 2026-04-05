# 🚀 部署到 Streamlit Cloud（免費）

讓朋友用手機或電腦瀏覽特價商品，完全免費！

---

## 📋 架構說明

```
你的電腦（每天執行爬蟲）
    ↓ git push 推送 JSON 資料到 GitHub
GitHub 倉庫（存放程式碼 + JSON 資料）
    ↓ Streamlit Cloud 自動讀取
朋友的手機/電腦（用網址瀏覽）
```

---

## 🔧 步驟一：初始化 Git（只需做一次）

在 VS Code 終端機執行：

```bash
cd "c:\Users\user\Desktop\cline\on sell tracker"
git init
git add .
git commit -m "初始化特價追蹤器"
```

---

## 🔧 步驟二：建立 GitHub 倉庫（只需做一次）

1. 前往 https://github.com → 點右上角 `+` → `New repository`
2. Repository name：`on-sell-tracker`
3. 選 **Public**（Streamlit Cloud 免費版需要公開）
4. **不要**勾選 Initialize README
5. 點 `Create repository`

建立後，GitHub 會顯示指令，執行：

```bash
git remote add origin https://github.com/你的帳號/on-sell-tracker.git
git branch -M main
git push -u origin main
```

---

## ☁️ 步驟三：部署到 Streamlit Cloud（只需做一次）

1. 前往 https://share.streamlit.io
2. 用 **GitHub 帳號**登入
3. 點 `New app`
4. 填入：
   - Repository：`你的帳號/on-sell-tracker`
   - Branch：`main`
   - Main file path：`app.py`
5. 點 `Deploy!`（等 2-3 分鐘）

部署完成後得到網址，例如：
```
https://你的帳號-on-sell-tracker-app-xxxxx.streamlit.app
```

**把這個網址分享給朋友！** 📱

---

## 🔄 每天更新資料（日常操作）

每次想更新資料，在你的電腦執行：

```bash
cd "c:\Users\user\Desktop\cline\on sell tracker"

# 執行爬蟲
python scraper_uniqlo_jp.py
python scraper_momo_muji.py

# 推送到 GitHub（Streamlit Cloud 自動更新）
git add *.json
git commit -m "更新特價資料"
git push
```

---

## 📱 手機加入主畫面（像 APP 一樣）

### iPhone（Safari）
1. 用 Safari 開啟網址
2. 點底部「分享」📤 → 「加入主畫面」→「新增」

### Android（Chrome）
1. 用 Chrome 開啟網址
2. 點右上角 ⋮ → 「新增至主畫面」→「新增」

---

## ⚠️ 注意事項

- **JSON 檔案大小**：目前各 JSON 都很小（< 200KB），可以正常上傳
- **Streamlit Cloud 免費版**：App 閒置 7 天後休眠，有人開啟時自動喚醒（約 30 秒）
- **daily_deals.json**（UNIQLO 台灣）已排除在 .gitignore，需要時再加回來
