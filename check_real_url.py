"""用 Playwright 從 UNIQLO 台灣特價頁面抓取真實商品連結格式"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 有頭模式看看
    page = browser.new_page()
    page.goto("https://www.uniqlo.com/tw/zh_TW/c/feature-sale-women.html", timeout=60000)
    # 等待商品卡片出現
    try:
        page.wait_for_selector("[class*='product']", timeout=20000)
    except:
        pass
    page.wait_for_timeout(5000)
    # 滾動頁面
    page.evaluate("window.scrollTo(0, 1000)")
    page.wait_for_timeout(3000)
    
    # 找所有 href
    all_links = page.eval_on_selector_all(
        "a",
        "els => els.map(e => e.href).filter(h => h && h.length > 10).slice(0, 30)"
    )
    print(f"找到 {len(all_links)} 個連結（前30個）：")
    for link in all_links:
        print(f"  {link}")
    
    # 找 data-href 或其他屬性
    data_links = page.eval_on_selector_all(
        "[data-href], [data-url], [data-link]",
        "els => els.slice(0, 10).map(e => e.dataset.href || e.dataset.url || e.dataset.link)"
    )
    if data_links:
        print(f"\ndata-href 連結：")
        for link in data_links:
            print(f"  {link}")
    
    # 頁面 HTML 中找 /products/ 路徑
    import re
    html = page.content()
    product_urls = re.findall(r'["\']([^"\']*?/products/[^"\']+)["\']', html)
    unique_urls = list(set(product_urls))[:10]
    print(f"\nHTML 中找到的 /products/ 路徑：")
    for u in unique_urls:
        print(f"  {u}")
    
    print(f"\n頁面標題: {page.title()}")
    
    browser.close()
