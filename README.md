# 🛍️ 特價商品追蹤器

每日自動抓取多品牌特價商品，透過 Streamlit 介面瀏覽、篩選、排序。

## 支援品牌

| 品牌 | 爬蟲 | 資料檔 | 說明 |
|------|------|--------|------|
| **UNIQLO 日本特賣** | `scraper_uniqlo_jp.py` | `uniqlo_jp_deals.json` | 日本官網女性特賣，¥ 日圓 |
| **momo 無印良品** | `scraper_momo_muji.py` | `momo_muji_deals.json` | momo 購物網無印良品特賣 |
| **UNIQLO 台灣女性特價** | `scraper.py` | `daily_deals.json` | 台灣官網女性特價 |

## 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt
playwright install chromium

# 執行爬蟲
python scraper_uniqlo_jp.py      # UNIQLO 日本
python scraper_momo_muji.py      # momo 無印良品
python scraper.py                # UNIQLO 台灣

# 啟動介面
streamlit run app.py
```

## 功能

- 🏪 **多品牌切換**：左側選擇品牌
- 📂 **分類篩選**：外套、上衣、褲子、裙子、洋裝等
- 💰 **價格範圍**：滑桿篩選價格
- 🔃 **排序**：現價低→高、高→低、折扣最多
- 🔄 **一鍵更新**：點擊更新按鈕即時抓取最新資料
- 🖼️ **商品圖片**：自動下載並顯示商品圖片

## 檔案結構

```
on sell tracker/
├── app.py                    # Streamlit 介面
├── scraper.py                # UNIQLO 台灣爬蟲
├── scraper_uniqlo_jp.py      # UNIQLO 日本爬蟲
├── scraper_momo_muji.py      # momo 無印良品爬蟲
├── daily_deals.json          # UNIQLO 台灣資料
├── uniqlo_jp_deals.json      # UNIQLO 日本資料
├── momo_muji_deals.json      # momo 無印良品資料
├── daily_deals.csv           # CSV 匯出（UNIQLO 台灣）
├── requirements.txt
└── .github/workflows/        # GitHub Actions 自動排程
```

## 技術

- **Python 3.11+**
- **Playwright**：動態頁面渲染、API 攔截
- **Streamlit**：Web 介面
- **requests**：圖片下載
