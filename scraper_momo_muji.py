"""
momo 購物 無印良品特賣爬蟲
目標：https://www.momoshop.com.tw/search/searchShop.jsp?keyword=無印良品&isDiscount=1
用 Playwright 渲染後抓取商品名稱、現價、原價、圖片、連結
排除：男裝、食品
輸出：momo_muji_deals.json
"""
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_JSON = "momo_muji_deals.json"

SEARCH_URL = (
    "https://www.momoshop.com.tw/search/searchShop.jsp"
    "?keyword=%E7%84%A1%E5%8D%B0%E8%89%AF%E5%93%81"
    "&searchType=1&isDiscount=1&showType=chessboardType"
    "&brandId=MUJI"
)
# 備用（不限品牌）
SEARCH_URL_FALLBACK = (
    "https://www.momoshop.com.tw/search/searchShop.jsp"
    "?keyword=%E7%84%A1%E5%8D%B0%E8%89%AF%E5%93%81"
    "&searchType=1&isDiscount=1&showType=chessboardType"
)

# 排除關鍵字（男裝、食品）
EXCLUDE_KEYWORDS = [
    "男", "男裝", "男款", "男性", "男生", "男士",
    "食品", "零食", "飲料", "咖啡", "茶", "餅乾", "糖果",
    "洗碗", "清潔", "廚房", "文具", "筆記", "收納盒", "資料夾",
    "床墊", "棉被", "枕頭", "毛巾", "浴巾",
]

CATEGORIES = {
    "外套": ["外套", "夾克", "大衣", "風衣", "羽絨", "Jacket", "Coat", "Parka", "Blouson"],
    "上衣": ["上衣", "T恤", "T-shirt", "Tee", "tee", "襯衫", "針織", "毛衣", "背心",
             "Shirt", "Blouse", "Knit", "Sweater", "Sweat", "Tank", "Polo"],
    "褲子": ["褲", "牛仔", "Pants", "Jeans", "Leggings", "Shorts"],
    "裙子": ["裙", "Skirt"],
    "洋裝": ["洋裝", "連身", "One-piece", "Dress"],
    "內搭": ["內搭", "內衣", "Bra"],
    "配件": ["圍巾", "帽子", "手套", "包包", "襪子", "皮帶", "Scarf", "Hat", "Bag", "Socks", "Belt"],
    "居家": ["收納", "整理", "置物", "架", "盒", "籃", "掛", "鉤"],
    "文具": ["筆", "本", "冊", "夾", "文具"],
    "美妝": ["乳液", "保濕", "護膚", "洗面", "化妝", "香皂", "沐浴"],
}

def classify(name: str) -> str:
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in name:
                return category
    return "其他"


def should_exclude(name: str) -> bool:
    for kw in EXCLUDE_KEYWORDS:
        if kw in name:
            return True
    return False


def scrape_momo_page(page, url: str, max_pages: int = 5) -> list:
    """用 Playwright 抓取 momo 頁面商品（支援翻頁）"""
    print(f"  [momo] 開啟: {url[:80]}")
    page.goto(url, timeout=30000)
    time.sleep(8)

    all_products = []
    current_page = 1

    while current_page <= max_pages:
        print(f"  [momo] 第 {current_page} 頁...")

        products = page.evaluate("""
            () => {
                const items = Array.from(document.querySelectorAll('li.listAreaLi'));
                return items.map(item => {
                    // goodsNo
                    const goodsNoInput = item.querySelector('input[name="viewProdId"]');
                    const goodsNo = goodsNoInput ? goodsNoInput.value : '';

                    // 圖片（goods-img class）
                    const goodsImg = item.querySelector('img.goods-img');
                    const imgSrc = goodsImg ? goodsImg.src : '';

                    // 名稱（從 img alt）
                    const name = goodsImg ? goodsImg.alt : '';

                    // 連結
                    const linkEl = item.querySelector('a.goods-img-url, a[href*="GoodsDetail"]');
                    const link = linkEl ? linkEl.href : (goodsNo ? `https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=${goodsNo}` : '');

                    // 價格（找含數字的文字）
                    const priceEls = Array.from(item.querySelectorAll('b, strong, [class*="price"], [class*="Price"]'));
                    const prices = priceEls.map(el => el.innerText.trim()).filter(t => /^[\\d,]+$/.test(t.replace(/[NT$,\\s]/g, '')));

                    // 原價（找 del 或 s 標籤）
                    const origEl = item.querySelector('del, s, [class*="origin"], [class*="Origin"]');
                    const origPrice = origEl ? origEl.innerText.trim() : '';

                    return { goodsNo, imgSrc, name, link, prices, origPrice };
                });
            }
        """)

        print(f"    找到 {len(products)} 件商品")
        all_products.extend(products)

        if len(products) == 0:
            break

        # 嘗試翻頁
        try:
            next_btn = page.query_selector("a.nextPage, button.nextPage, [class*='next']:not([disabled])")
            if next_btn:
                next_btn.click()
                time.sleep(5)
                current_page += 1
            else:
                break
        except:
            break

    return all_products


def scrape():
    print("=" * 60)
    print("  momo 無印良品特賣爬蟲")
    print(f"  執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_raw = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="zh-TW",
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
        page = context.new_page()

        raw = scrape_momo_page(page, SEARCH_URL_FALLBACK, max_pages=10)
        all_raw.extend(raw)

        browser.close()

    # 整理資料
    seen = set()
    products = []
    excluded = 0

    for r in all_raw:
        name = (r.get("name") or "").strip()
        goods_no = r.get("goodsNo", "")
        link = r.get("link", "")

        if not name or goods_no in seen:
            continue

        # 過濾非無印良品商品
        if "無印良品" not in name and "MUJI" not in name:
            continue

        # 排除男裝、食品
        if should_exclude(name):
            excluded += 1
            continue

        seen.add(goods_no)

        # 解析價格
        prices = r.get("prices", [])
        nums = []
        for p_str in prices:
            m = re.findall(r"[\d,]+", p_str)
            for n in m:
                try:
                    nums.append(int(n.replace(",", "")))
                except:
                    pass
        nums = sorted(set(nums))
        current = str(nums[0]) if nums else ""

        orig_str = r.get("origPrice", "")
        orig_nums = re.findall(r"[\d,]+", orig_str)
        original = str(int(orig_nums[0].replace(",", ""))) if orig_nums else (str(nums[-1]) if len(nums) > 1 else "")

        # 圖片 URL（momo 圖片可直接存取）
        img_url = r.get("imgSrc", "")

        products.append({
            "品牌": "momo 無印良品",
            "分類": classify(name),
            "商品名稱": name,
            "現價": current,
            "原價": original,
            "圖片網址": img_url,
            "商品連結": link,
        })

    print(f"\n[統計] 共 {len(products)} 件商品（排除 {excluded} 件）")
    cat_count = Counter(p["分類"] for p in products)
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat:<8}：{cnt} 件")

    # 儲存 JSON
    output = {
        "brand": "momo 無印良品",
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
