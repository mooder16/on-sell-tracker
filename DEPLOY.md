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

## 🔧 步驟一：申請 GitHub 帳號（免費）

1. 前往 https://github.com
2. 點右上角 **Sign up**
3. 填入：
   - Username（帳號名稱，例如 `alice123`）
   - Email
   - Password
4. 完成驗證，帳號就建立好了！

---

## 🔧 步驟二：建立 GitHub 倉庫

1. 登入 GitHub 後，點右上角 `+` → `New repository`
2. 填入：
   - Repository name：`on-sell-tracker`
   - 選 **Public**（必須公開，Streamlit Cloud 免費版才能讀取）
   - **不要**勾選 "Add a README file"
3. 點 `Create repository`

---

## 🔧 步驟三：上傳程式碼到 GitHub

建立倉庫後，在 VS Code 終端機執行（把 `你的帳號` 換成你的 GitHub 帳號名稱）：

```bash
cd "c:\Users\user\Desktop\cline\on sell tracker"
git remote add origin https://github.com/你的帳號/on-sell-tracker.git
git branch -M main
git push -u origin main
```

> 第一次 push 時，會彈出視窗要求登入 GitHub，用瀏覽器登入即可。

---

## ☁️ 步驟四：部署到 Streamlit Cloud

1. 前往 https://share.streamlit.io
2. 點 **Continue with GitHub** → 用 GitHub 帳號登入
3. 點 `New app`
4. 填入：
   - Repository：選 `你的帳號/on-sell-tracker`
   - Branch：`main`
   - Main file path：`app.py`
5. 點 `Deploy!`（等 2-3 分鐘）

部署完成後得到網址，例如：
```
https://alice123-on-sell-tracker-app-xxxxx.streamlit.app
```

**把這個網址分享給朋友！** 📱

---

## 📱 手機加入主畫面（像 APP 一樣）

### iPhone（Safari）
1. 用 Safari 開啟網址
2. 點底部「分享」📤 → 「加入主畫面」→「新增」

### Android（Chrome）
1. 用 Chrome 開啟網址
2. 點右上角 ⋮ → 「新增至主畫面」→「新增」

加入後就像 APP 一樣出現在主畫面！

---

## 🔄 每天更新資料（日常操作）

每次想更新資料，在 VS Code 終端機執行：

```bash
cd "c:\Users\user\Desktop\cline\on sell tracker"

# 執行爬蟲（約 5-10 分鐘）
python scraper_uniqlo_jp.py
python scraper_momo_muji.py

# 推送到 GitHub（Streamlit Cloud 自動更新）
git add *.json
git commit -m "更新特價資料"
git push
```

朋友重新整理頁面就能看到最新資料！

---

## ⚠️ 常見問題

**Q：朋友說網頁很慢？**
A：第一次開啟需要喚醒 App（約 30 秒），之後就快了。

**Q：App 閒置後休眠怎麼辦？**
A：有人開啟時會自動喚醒，等 30 秒即可。

**Q：push 時要求輸入密碼？**
A：GitHub 現在用 Token 取代密碼。如果要求輸入密碼，請到 GitHub → Settings → Developer settings → Personal access tokens → 產生一個 Token，用 Token 當密碼。
