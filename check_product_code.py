import json
import urllib.request

API_URL = "https://d.uniqlo.com/tw/p/search/products/by-category"
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.uniqlo.com",
    "Referer": "https://www.uniqlo.com/tw/zh_TW/c/feature-sale-women.html",
}

payload = {
    "pageInfo": {"page": 1, "pageSize": 3},
    "belongTo": "pc",
    "rank": "overall",
    "priceRange": {"low": 0, "high": 0},
    "color": [], "size": [], "identity": [], "exist": [],
    "categoryCode": "feature-sale-women",
    "searchFlag": False,
    "description": "",
    "stockFilter": "warehouse",
}

body = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(API_URL, data=body, headers=API_HEADERS, method="POST")
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))

items = data["resp"][0]["productList"]
print("前3件商品的所有欄位值：")
for item in items[:2]:
    print(f"\n=== {item.get('name', '')} ===")
    for k, v in item.items():
        if v and k not in ['sizeSequence', 'colorPic', 'colorShow', 'prices', 'stores', 'topCategories', 'categorySortList']:
            print(f"  {k}: {v}")
