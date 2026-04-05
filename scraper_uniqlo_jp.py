"""
UNIQLO 日本爬蟲
抓取兩個頁面：
  1. 特賣（セール）：https://www.uniqlo.com/jp/ja/feature/sale/women
  2. 期間限定特價：https://www.uniqlo.com/jp/ja/feature/limited-offers/women
輸出：
  uniqlo_jp_deals.json        （特賣）
  uniqlo_jp_limited.json      （期間限定特價）
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRODUCT_API = "https://www.uniqlo.com/jp/api/commerce/v5/ja/products"

PAGES = [
    {
        "name": "UNIQLO 日本特賣",
        "url": "https://www.uniqlo.com/jp/ja/feature/sale/women",
        "output": "uniqlo_jp_deals.json",
    },
    {
        "name": "UNIQLO 日本期間限定特價",
        "url": "https://www.uniqlo.com/jp/ja/feature/limited-offers/women",
        "output": "uniqlo_jp_limited.json",
    },
]

CATEGORIES = {
    "外套": ["コート", "ジャケット", "アウター", "ブルゾン", "ダウン", "パーカ", "ウインドブレーカー"],
    "上衣": ["Tシャツ", "ニット", "セーター", "ブラウス", "シャツ", "カットソー", "スウェット",
             "タンクトップ", "ポロ", "トップス", "プルオーバー"],
    "褲子": ["パンツ", "ジーンズ", "デニム", "レギンス", "ショーツ", "ショートパンツ"],
    "裙子": ["スカート"],
    "洋裝": ["ワンピース", "ドレス"],
    "內搭": ["インナー", "ブラ", "下着", "ヒートテック"],
    "配件": ["スカーフ", "帽子", "手袋", "バッグ", "ソックス", "靴下", "ベルト"],
}

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Referer": "https://www.uniqlo.com/jp/",
}


def classify(name: str) -> str:
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in name:
                return category
    return "其他"


def fetch_products_by_ids(product_ids: list) -> list:
    all_items = []
    batch_size = 20
    for i in range(0, len(product_ids), batch_size):
        batch = product_ids[i:i+batch_size]
        ids_str = "%2C".join(urllib.parse.quote(pid) for pid in batch)
        url = f"{PRODUCT_API}?productIds={ids_str}"
        req = urllib.request.Request(url, headers=API_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8", errors="ignore")
                d = json.loads(body)
                items = d.get("result", {}).get("items", [])
                all_items.extend(items)
                print(f"  [API] 批次 {i//batch_size+1}：取得 {len(items)} 件")
        except Exception as e:
            print(f"  [API] 批次 {i//batch_size+1} 失敗：{str(e)[:60]}")
        time.sleep(0.3)
    return all_items


def get_product_image_url(item: dict) -> str:
    images = item.get("images", {})
    main = images.get("main", {})
    if not main:
        return ""
    for color_code, img_data in main.items():
        img_url = img_data.get("image", "")
        if img_url:
            return img_url
    return ""


def scrape_page(page_cfg: dict) -> list:
    """抓取單一頁面"""
    brand_name = page_cfg["name"]
    target_url = page_cfg["url"]
    output_json = page_cfg["output"]

    print(f"\n{'='*60}")
    print(f"  {brand_name}")
    print(f"  執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    all_product_ids = []
    intercepted_items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ja-JP",
        )
        page = context.new_page()

        def on_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if response.status == 200 and "json" in ct and "products?productIds=" in url:
                try:
                    body = response.body()
                    d = json.loads(body)
                    items = d.get("result", {}).get("items", [])
                    if items:
                        intercepted_items.extend(items)
                        print(f"  [攔截] {len(items)} 件商品")
                except:
                    pass

        page.on("response", on_response)

        print(f"  [開啟] {target_url}")
        page.goto(target_url, timeout=30000)
        time.sleep(8)

        cur_url = page.url
        title = page.title()
        if "not-found" in cur_url or "404" in title.lower():
            print(f"  [警告] 頁面不存在：{cur_url}")
            browser.close()
            return []

        print(f"  [標題] {title[:60]}")

        print("  [滾動] 載入更多商品...")
        prev_count = 0
        for scroll_i in range(25):
            page.evaluate(f"window.scrollTo(0, {(scroll_i+1)*1200})")
            time.sleep(1.5)
            count = page.evaluate(
                "() => document.querySelectorAll('a[href*=\"/products/\"]').length"
            )
            if count == prev_count and scroll_i > 5:
                print(f"  [滾動] 商品數不再增加（{count}），停止")
                break
            prev_count = count

        time.sleep(3)

        dom_data = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href*="/products/"]'));
                const ids = [...new Set(links.map(a => {
                    const m = a.href.match(/\\/products\\/([A-Z0-9-]+)/);
                    return m ? m[1] : null;
                }).filter(Boolean))];

                const allText = document.body.innerText || '';
                const globalDateMatch = allText.match(/(\\d{1,2}\\/\\d{1,2})まで/);
                const globalDate = globalDateMatch ? globalDateMatch[1] + 'まで' : '';

                const limitMap = {};
                const allCards = Array.from(document.querySelectorAll('li, article, [class*="product"], [class*="item"]'));
                for (const card of allCards) {
                    const text = card.innerText || '';
                    const dateMatch = text.match(/(\\d{1,2}\\/\\d{1,2})まで/);
                    if (!dateMatch) continue;
                    const linkEl = card.querySelector('a[href*="/products/"]');
                    if (!linkEl) continue;
                    const idMatch = linkEl.href.match(/\\/products\\/([A-Z0-9-]+)/);
                    if (idMatch) {
                        limitMap[idMatch[1]] = dateMatch[1] + 'まで';
                    }
                }
                return { ids, limitMap, globalDate };
            }
        """)
        all_product_ids = dom_data["ids"]
        limit_map = dom_data["limitMap"]
        global_date = dom_data.get("globalDate", "")
        print(f"  [DOM] 找到 {len(all_product_ids)} 個商品 ID")
        print(f"  [DOM] 全域截止日期: {global_date}")
        print(f"  [DOM] 個別截止日期: {len(limit_map)} 個")
        browser.close()

    # 補齊缺少的商品
    intercepted_ids = {item.get("productId", "") for item in intercepted_items}
    missing_ids = [pid for pid in all_product_ids if pid not in intercepted_ids]
    print(f"  [攔截] {len(intercepted_items)} 件 / 需補查 {len(missing_ids)} 件")

    if missing_ids:
        extra_items = fetch_products_by_ids(missing_ids)
        intercepted_items.extend(extra_items)

    # 整理資料
    seen = set()
    products = []
    for item in intercepted_items:
        product_id = item.get("productId", "")
        if not product_id or product_id in seen:
            continue
        seen.add(product_id)

        name = item.get("name", "").strip()
        if not name:
            continue

        prices = item.get("prices") or {}
        base_obj = prices.get("base") or {}
        promo_obj = prices.get("promo") or {}
        base_price = base_obj.get("value", 0) or 0
        promo_price = promo_obj.get("value", 0) or 0

        current = str(promo_price) if promo_price else str(base_price)
        original = str(base_price) if base_price and base_price != promo_price else ""

        img_url = get_product_image_url(item)
        product_url = f"https://www.uniqlo.com/jp/ja/products/{product_id}/00"
        limit_until = limit_map.get(product_id, "") or global_date

        products.append({
            "品牌": brand_name,
            "分類": classify(name),
            "商品名稱": name,
            "現價": current,
            "原價": original,
            "截止日期": limit_until,
            "圖片網址": img_url,
            "商品連結": product_url,
        })

    print(f"\n[統計] 共 {len(products)} 件商品")
    cat_count = Counter(p["分類"] for p in products)
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat:<8}：{cnt} 件")

    output = {
        "brand": brand_name,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(products),
        "products": products,
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 已儲存：{output_json}（{len(products)} 筆）")
    return products


def scrape():
    for page_cfg in PAGES:
        scrape_page(page_cfg)


if __name__ == "__main__":
    scrape()
