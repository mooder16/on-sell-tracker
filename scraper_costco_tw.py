"""
Costco 台灣特價爬蟲
目標頁面：
  1. 每日精選優惠：https://www.costco.com.tw/Daily-Deals/c/Coupon
  2. 降價商品：https://www.costco.com.tw/c/new_lower_prices
用 Playwright 渲染後抓取商品名稱、現價、原價、圖片、連結
輸出：costco_tw_deals.json
"""
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_JSON = "costco_tw_deals.json"

PAGES = [
    {
        "name": "Costco 每日精選優惠",
        "url": "https://www.costco.com.tw/Daily-Deals/c/Coupon",
    },
    {
        "name": "Costco 降價商品",
        "url": "https://www.costco.com.tw/c/new_lower_prices",
    },
]

CATEGORIES = {
    "食品": ["食品", "零食", "餅乾", "糖果", "咖啡", "茶", "飲料", "果汁", "牛奶", "優格",
             "堅果", "杏仁", "腰果", "花生", "巧克力", "糖", "蜂蜜", "醬", "油", "米",
             "麵", "罐頭", "湯", "調味", "香料", "烘焙", "麵包", "蛋糕", "冷凍", "海鮮",
             "肉", "雞", "牛", "豬", "魚", "蝦", "Almonds", "Cashews", "Nuts", "Coffee",
             "Tea", "Juice", "Milk", "Yogurt", "Chocolate", "Honey", "Sauce", "Oil"],
    "清潔": ["清潔", "洗碗", "洗衣", "洗手", "洗髮", "沐浴", "肥皂", "香皂", "洗劑",
             "漂白", "消毒", "除菌", "衛生紙", "紙巾", "廚房紙", "垃圾袋",
             "Detergent", "Soap", "Shampoo", "Conditioner", "Bleach"],
    "美妝保養": ["乳液", "保濕", "護膚", "化妝", "面膜", "精華", "防曬", "卸妝",
                "護手", "護唇", "香水", "彩妝", "粉底", "口紅", "睫毛",
                "Moisturizer", "Serum", "Sunscreen", "Lotion", "Cream", "Cetaphil",
                "Neutrogena", "Olay", "L'Oreal"],
    "健康保健": ["維他命", "維生素", "魚油", "益生菌", "膠原蛋白", "葉黃素", "鈣",
                "鐵", "鋅", "蛋白質", "保健", "藥", "醫療", "口罩",
                "Vitamin", "Fish Oil", "Probiotic", "Collagen", "Calcium", "Protein",
                "Supplement", "Omega"],
    "家電": ["電視", "冰箱", "洗衣機", "烘衣機", "冷氣", "空調", "除濕", "空氣清淨",
             "吸塵器", "掃地機", "電鍋", "烤箱", "微波爐", "咖啡機", "果汁機",
             "吹風機", "電熱水壺", "充電", "耳機", "喇叭", "相機",
             "TV", "Washer", "Dryer", "Vacuum", "Blender", "Mixer", "Heater",
             "Samsung", "LG", "Dyson", "Philips", "Panasonic", "Sony"],
    "3C": ["筆電", "電腦", "平板", "手機", "iPad", "iPhone", "MacBook", "Surface",
           "鍵盤", "滑鼠", "螢幕", "硬碟", "記憶體", "USB", "充電器",
           "Laptop", "Tablet", "Monitor", "Keyboard", "Mouse", "SSD", "HDD"],
    "服飾": ["衣", "褲", "裙", "外套", "夾克", "T恤", "Polo", "襯衫", "毛衣",
             "內衣", "內褲", "襪子", "鞋", "帽子", "圍巾", "手套",
             "Shirt", "Pants", "Jacket", "Coat", "Socks", "Shoes", "Hat"],
    "居家": ["床", "枕頭", "棉被", "毛巾", "浴巾", "地墊", "窗簾", "燈", "椅",
             "桌", "架", "收納", "置物", "掛", "鉤", "鏡", "時鐘",
             "Pillow", "Blanket", "Towel", "Lamp", "Chair", "Table", "Storage"],
    "戶外運動": ["運動", "健身", "瑜珈", "自行車", "登山", "露營", "帳篷", "睡袋",
                "球", "球拍", "游泳", "跑步", "健走",
                "Sports", "Fitness", "Yoga", "Bike", "Camping", "Tent", "Golf"],
    "寵物": ["寵物", "狗", "貓", "飼料", "零食", "玩具", "貓砂",
             "Pet", "Dog", "Cat", "Food", "Treat"],
    "汽車": ["汽車", "車", "輪胎", "機油", "雨刷", "座椅", "行車記錄",
             "Car", "Tire", "Motor Oil", "Wiper"],
}


def classify(name: str) -> str:
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in name.lower():
                return category
    return "其他"


def scrape_costco_page(page, url: str, source_name: str) -> list:
    """用 Playwright 抓取 Costco 頁面商品（支援無限滾動）"""
    print(f"  [Costco] 開啟: {url}")
    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(5)
    except Exception as e:
        print(f"  [Costco] 頁面載入失敗: {e}")
        return []

    # 滾動頁面載入更多商品
    print("  [Costco] 滾動載入商品...")
    prev_count = 0
    for scroll_i in range(15):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        count = page.evaluate("""
            () => document.querySelectorAll(
                'li.product, .product-item, [class*="product"], li[class*="item"]'
            ).length
        """)
        print(f"    滾動 {scroll_i+1}：找到 {count} 件")
        if count == prev_count and scroll_i > 3:
            break
        prev_count = count

    # 抓取商品資料
    products = page.evaluate("""
        (sourceName) => {
            // Costco TW 使用 SAP Commerce Cloud，商品在 li.product 或類似容器
            const selectors = [
                'li.product',
                '.product-item',
                'li[class*="product"]',
                '[data-product-code]',
                '.product-tile',
                'li.item',
            ];

            let items = [];
            for (const sel of selectors) {
                const found = document.querySelectorAll(sel);
                if (found.length > 2) {
                    items = Array.from(found);
                    break;
                }
            }

            return items.map(item => {
                // 商品名稱
                const nameEl = item.querySelector(
                    '.product-name, .productName, h2, h3, h4, ' +
                    '[class*="name"], [class*="title"], a[title]'
                );
                const name = nameEl
                    ? (nameEl.getAttribute('title') || nameEl.innerText || '').trim()
                    : '';

                // 現價
                const priceEl = item.querySelector(
                    '.price, .current-price, .sale-price, ' +
                    '[class*="price"]:not([class*="origin"]):not([class*="was"]):not([class*="old"])'
                );
                const priceText = priceEl ? priceEl.innerText.trim() : '';

                // 原價
                const origEl = item.querySelector(
                    '.original-price, .was-price, .old-price, del, s, ' +
                    '[class*="origin"], [class*="was"], [class*="old"], [class*="before"]'
                );
                const origText = origEl ? origEl.innerText.trim() : '';

                // 圖片
                const imgEl = item.querySelector('img');
                const imgSrc = imgEl
                    ? (imgEl.getAttribute('data-src') || imgEl.getAttribute('src') || '')
                    : '';

                // 連結
                const linkEl = item.querySelector('a[href]');
                const href = linkEl ? linkEl.getAttribute('href') : '';
                const link = href
                    ? (href.startsWith('http') ? href : 'https://www.costco.com.tw' + href)
                    : '';

                // 商品代碼
                const code = item.getAttribute('data-product-code') ||
                             item.getAttribute('data-code') || '';

                return { name, priceText, origText, imgSrc, link, code, source: sourceName };
            });
        }
    """, source_name)

    print(f"  [Costco] 抓到 {len(products)} 筆原始資料")
    return products


def parse_price(text: str) -> str:
    """從文字中提取數字價格"""
    if not text:
        return ""
    nums = re.findall(r"[\d,]+", text.replace("NT$", "").replace("$", ""))
    for n in nums:
        try:
            val = int(n.replace(",", ""))
            if val > 0:
                return str(val)
        except Exception:
            pass
    return ""


def scrape():
    print("=" * 60)
    print("  Costco 台灣特價爬蟲")
    print(f"  執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_raw = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="zh-TW",
            extra_http_headers={
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            },
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
        page = context.new_page()

        for page_cfg in PAGES:
            print(f"\n── {page_cfg['name']} ──")
            raw = scrape_costco_page(page, page_cfg["url"], page_cfg["name"])
            all_raw.extend(raw)

        browser.close()

    # 整理資料
    seen = set()
    products = []

    for r in all_raw:
        name = (r.get("name") or "").strip()
        if not name or len(name) < 3:
            continue

        link = r.get("link", "")
        # 去重（用名稱+連結）
        key = name[:30]
        if key in seen:
            continue
        seen.add(key)

        current = parse_price(r.get("priceText", ""))
        original = parse_price(r.get("origText", ""))

        # 如果原價 <= 現價，清空原價
        try:
            if original and current and int(original) <= int(current):
                original = ""
        except Exception:
            pass

        img_url = r.get("imgSrc", "")
        # 修正相對路徑圖片
        if img_url and img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url and not img_url.startswith("http"):
            img_url = "https://www.costco.com.tw" + img_url

        source = r.get("source", "Costco 台灣")

        products.append({
            "品牌": "Costco 台灣",
            "來源": source,
            "分類": classify(name),
            "商品名稱": name,
            "現價": current,
            "原價": original,
            "圖片網址": img_url,
            "商品連結": link,
        })

    print(f"\n[統計] 共 {len(products)} 件商品")
    cat_count = Counter(p["分類"] for p in products)
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat:<8}：{cnt} 件")

    # 儲存 JSON
    output = {
        "brand": "Costco 台灣",
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(products),
        "products": products,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 已儲存：{OUTPUT_JSON}（{len(products)} 筆）")
    return products


if __name__ == "__main__":
    scrape()
