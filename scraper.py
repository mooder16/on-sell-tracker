"""
UNIQLO 女性特價商品爬蟲
目標：https://www.uniqlo.com/tw/zh_TW/c/feature-sale-women.html
API：POST https://d.uniqlo.com/tw/p/search/products/by-category
抓取：商品名稱、現價、原價、圖片（base64）、商品連結
分類：外套、上衣、褲子、裙子、洋裝、內搭、配件、其他
輸出：daily_deals.csv、daily_deals.json
"""

import csv
import json
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime

# 強制 stdout 使用 utf-8（避免 Windows cp950 emoji 錯誤）
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 設定 ──────────────────────────────────────────────────────
API_URL = "https://d.uniqlo.com/tw/p/search/products/by-category"
IMAGE_BASE = "https://www.uniqlo.com/tw"
PRODUCT_URL_BASE = "https://www.uniqlo.com/tw/zh_TW/products/{product_code}/select"
OUTPUT_CSV = "daily_deals.csv"
OUTPUT_JSON = "daily_deals.json"
CATEGORY_CODE = "feature-sale-women"
PAGE_SIZE = 36

CATEGORIES = {
    "外套": ["外套", "夾克", "大衣", "風衣", "羽絨", "防風", "防寒",
             "Jacket", "jacket", "Coat", "coat", "Parka", "parka", "Blouson", "blouson"],
    "上衣": ["上衣", "T恤", "T-shirt", "Tee", "tee", "襯衫", "針織", "毛衣",
             "衛衣", "帽T", "背心", "Shirt", "shirt", "Blouse", "blouse",
             "Knit", "knit", "Sweater", "sweater", "Sweat", "sweat", "Tank", "tank", "Polo", "polo"],
    "褲子": ["褲", "牛仔", "Pants", "pants", "Jeans", "jeans",
             "Leggings", "leggings", "Shorts", "shorts"],
    "裙子": ["裙", "Skirt", "skirt"],
    "洋裝": ["洋裝", "連身", "One-piece", "one-piece", "Dress", "dress"],
    "內搭": ["內搭", "內衣", "Innerwear", "innerwear", "Bra", "bra"],
    "配件": ["圍巾", "帽子", "手套", "包包", "襪子", "皮帶",
             "Scarf", "scarf", "Hat", "hat", "Gloves", "gloves",
             "Bag", "bag", "Socks", "socks", "Belt", "belt"],
}

API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.uniqlo.com",
    "Referer": "https://www.uniqlo.com/tw/zh_TW/c/feature-sale-women.html",
}

def classify(name: str) -> str:
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in name:
                return category
    return "其他"


def build_image_url(main_pic: str) -> str:
    if not main_pic:
        return ""
    if main_pic.startswith("http"):
        return main_pic
    return IMAGE_BASE + main_pic


def build_product_url(product_code: str) -> str:
    if not product_code:
        return ""
    return PRODUCT_URL_BASE.format(product_code=product_code)


def fetch_page(page: int, page_size: int = PAGE_SIZE) -> dict:
    payload = {
        "pageInfo": {"page": page, "pageSize": page_size},
        "belongTo": "pc",
        "rank": "overall",
        "priceRange": {"low": 0, "high": 0},
        "color": [], "size": [], "identity": [], "exist": [],
        "categoryCode": CATEGORY_CODE,
        "searchFlag": False,
        "description": "",
        "stockFilter": "warehouse",
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers=API_HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_products(data: dict) -> list:
    products = []
    try:
        items = data["resp"][0]["productList"]
    except (KeyError, IndexError):
        return products

    for item in items:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or item.get("productName") or "").strip()
        current_price = str(item["minPrice"]) if item.get("minPrice") is not None else ""
        original_price = str(item["originPrice"]) if item.get("originPrice") is not None else ""
        image_url = build_image_url(item.get("mainPic", ""))
        product_url = build_product_url(item.get("productCode", ""))

        if name:
            products.append({
                "分類": classify(name),
                "商品名稱": name,
                "現價": current_price,
                "原價": original_price,
                "圖片網址": image_url,
                "商品連結": product_url,
            })
    return products


def scrape():
    print("=" * 60)
    print("  UNIQLO 女性特價商品爬蟲")
    print(f"  執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\n[API] {API_URL}")
    print(f"[分類] {CATEGORY_CODE}\n")

    all_products = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        print(f"[取得] 第 {page}/{total_pages} 頁...")
        try:
            data = fetch_page(page)
            if page == 1:
                try:
                    total = data["resp"][0].get("productSum", 0)
                    if total:
                        total_pages = (int(total) + PAGE_SIZE - 1) // PAGE_SIZE
                        print(f"   共 {total} 件商品，{total_pages} 頁")
                except Exception:
                    pass

            products = parse_products(data)
            print(f"   解析到 {len(products)} 件商品")
            all_products.extend(products)

            if not products:
                break
            page += 1
            if page <= total_pages:
                time.sleep(0.5)

        except urllib.error.HTTPError as e:
            print(f"   [錯誤] HTTP {e.code}: {e.reason}")
            break
        except Exception as e:
            print(f"   [錯誤] {e}")
            break

    # 去重
    seen = set()
    unique_products = []
    for p in all_products:
        if p["商品名稱"] not in seen:
            seen.add(p["商品名稱"])
            unique_products.append(p)

    # 統計
    print(f"\n[統計] 分類統計：")
    print("-" * 30)
    cat_count = Counter(p["分類"] for p in unique_products)
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat:<8}：{count} 件")
    print(f"  {'合計':<8}：{len(unique_products)} 件")
    print("-" * 30)

    if unique_products:
        # 儲存 CSV
        csv_fields = ["分類", "商品名稱", "現價", "原價", "圖片網址", "商品連結"]
        try:
            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(unique_products)
            print(f"\n[OK] CSV 已儲存：{OUTPUT_CSV}（{len(unique_products)} 筆）")
        except PermissionError:
            print(f"\n[!] CSV 儲存失敗（檔案被佔用），請關閉 Excel 後重試")

        # 儲存 JSON（不含 base64，只存圖片 URL）
        output_data = {
            "brand": "UNIQLO 台灣女性特價",
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(unique_products),
            "products": unique_products,
        }
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON 已儲存：{OUTPUT_JSON}（{len(unique_products)} 筆）")
    else:
        print("\n[!] 未找到任何商品資料")

    print("\n[完成] 爬蟲執行完畢！")
    return unique_products


if __name__ == "__main__":
    scrape()
