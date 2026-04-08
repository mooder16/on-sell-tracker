"""
特價商品瀏覽介面（多品牌）
支援：UNIQLO 日本特賣、UNIQLO 日本期間限定特價、momo 無印良品、UNIQLO 台灣
資料由 GitHub Actions 每4小時自動更新
"""
import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="特價商品追蹤",
    page_icon="🛍️",
    layout="wide",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* 整體背景 */
.stApp { background-color: #f0f0f0; }

/* 商品卡片容器 */
.product-card {
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
    margin-bottom: 4px;
    transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
}

/* 卡片圖片 */
.product-card img {
    width: 100%;
    aspect-ratio: 1/1;
    object-fit: cover;
    display: block;
}

/* 卡片文字區 */
.card-body {
    padding: 10px 12px 14px;
    background: #ffffff;
}
.card-name {
    font-size: 13px;
    font-weight: 600;
    color: #111111;
    margin: 6px 0 8px;
    line-height: 1.4;
    min-height: 36px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.card-price {
    margin-bottom: 10px;
    line-height: 1.8;
}
.price-current {
    font-size: 22px;
    font-weight: 800;
    color: #cc0000;
}
.price-currency {
    font-size: 13px;
    font-weight: 700;
    color: #cc0000;
}
.price-original {
    font-size: 12px;
    color: #999;
    text-decoration: line-through;
    margin-left: 6px;
}
.price-discount {
    display: inline-block;
    background: #cc0000;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 4px;
    vertical-align: middle;
}
.limit-badge {
    display: inline-block;
    background: #ff6600;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 4px;
}
.btn-buy {
    display: block;
    text-align: center;
    background: #222222;
    color: #ffffff !important;
    text-decoration: none !important;
    padding: 9px 0;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    transition: background 0.2s;
}
.btn-buy:hover { background: #cc0000; }
.category-badge {
    display: inline-block;
    background: #eeeeee;
    color: #555555;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 20px;
    margin-right: 4px;
}
.brand-badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    margin-right: 4px;
}
.brand-uniqlo  { background: #cc0000; color: #fff; }
.brand-limited { background: #ff6600; color: #fff; }
.brand-momo    { background: #e91e8c; color: #fff; }
.brand-muji    { background: #8b7355; color: #fff; }
.brand-costco  { background: #005daa; color: #fff; }

/* 頁首 */
.page-header {
    padding: 10px 0 18px;
    border-bottom: 3px solid #cc0000;
    margin-bottom: 24px;
}
.page-title   { font-size: 26px; font-weight: 800; color: #111; margin: 0; }
.page-subtitle { font-size: 13px; color: #888; margin-top: 4px; }

/* 統計列 */
.stats-bar {
    background: #fff;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 14px;
    color: #555;
}

/* 自動更新提示 */
.auto-update-info {
    background: #e8f4fd;
    border: 1px solid #b3d7f0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #2a6496;
    margin-bottom: 8px;
}

/* 讓 st.image 填滿欄位 */
[data-testid="stImage"] img {
    width: 100% !important;
    aspect-ratio: 1/1;
    object-fit: cover;
    border-radius: 12px 12px 0 0;
    display: block;
}
[data-testid="stImage"] {
    margin-bottom: 0 !important;
    line-height: 0;
}
/* 移除 st.columns 的預設間距 */
[data-testid="column"] > div:first-child {
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── 品牌設定 ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

BRANDS = {
    "UNIQLO 日本特賣": {
        "json": BASE_DIR / "uniqlo_jp_deals.json",
        "badge_class": "brand-uniqlo",
        "color": "#cc0000",
        "currency": "¥",
    },
    "UNIQLO 日本期間限定特價": {
        "json": BASE_DIR / "uniqlo_jp_limited.json",
        "badge_class": "brand-limited",
        "color": "#ff6600",
        "currency": "¥",
    },
    "momo 無印良品": {
        "json": BASE_DIR / "momo_muji_deals.json",
        "badge_class": "brand-momo",
        "color": "#e91e8c",
        "currency": "NT$",
    },
    "UNIQLO 台灣女性特價": {
        "json": BASE_DIR / "daily_deals.json",
        "badge_class": "brand-uniqlo",
        "color": "#cc0000",
        "currency": "NT$",
    },
    "Costco 台灣特價": {
        "json": BASE_DIR / "costco_tw_deals.json",
        "badge_class": "brand-costco",
        "color": "#005daa",
        "currency": "NT$",
    },
}


@st.cache_data(ttl=300)
def load_data(json_path: str):
    p = Path(json_path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def render_card(product, badge_class, currency, brand_name):
    """輸出完整卡片（圖片 + 文字，一個 st.markdown 呼叫）"""
    name = product.get("商品名稱", "")
    current = product.get("現價", "")
    original = product.get("原價", "")
    image_url = product.get("圖片網址", "")
    product_url = product.get("商品連結", "")
    category = product.get("分類", "其他")
    brand = product.get("品牌", brand_name)
    limit_until = product.get("截止日期", "")

    # 折扣
    discount_html = ""
    try:
        c, o = int(current), int(original)
        if o > c > 0:
            pct = round((1 - c / o) * 100)
            discount_html = f'<span class="price-discount">-{pct}%</span>'
    except Exception:
        pass

    orig_html = (
        f'<span class="price-original">{currency}{original}</span>'
        if original and original != current else ""
    )
    price_html = (
        f'<span class="price-currency">{currency}</span>'
        f'<span class="price-current">{current}</span>'
        if current else '<span style="color:#aaa">價格未知</span>'
    )
    limit_html = (
        f'<div><span class="limit-badge">⏰ {limit_until}期間限定</span></div>'
        if limit_until else ""
    )
    btn_html = (
        f'<a href="{product_url}" target="_blank" class="btn-buy">前往購買 →</a>'
        if product_url else '<span style="color:#ccc;font-size:12px">無連結</span>'
    )

    # 圖片區：用 background-image 避免 <img> 被 Streamlit 過濾
    if image_url:
        img_section = (
            f'<div style="width:100%;aspect-ratio:1/1;'
            f'background-image:url(\'{image_url}\');'
            f'background-size:cover;background-position:center;'
            f'background-repeat:no-repeat;"></div>'
        )
    else:
        img_section = '<div style="width:100%;aspect-ratio:1/1;background:#f5f5f5;display:flex;align-items:center;justify-content:center;font-size:40px;">👗</div>'

    st.markdown(
        f"""<div class="product-card">
{img_section}
<div class="card-body">
<span class="brand-badge {badge_class}">{brand}</span><span class="category-badge">{category}</span>
{limit_html}
<div class="card-name">{name}</div>
<div class="card-price">{price_html} {orig_html} {discount_html}</div>
{btn_html}
</div></div>""",
        unsafe_allow_html=True,
    )


# ── 側邊欄 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ 特價商品追蹤")
    st.markdown("---")
    st.markdown("### 🏪 選擇品牌")
    selected_brand = st.radio("品牌", list(BRANDS.keys()), label_visibility="collapsed")

    brand_cfg = BRANDS[selected_brand]
    data = load_data(str(brand_cfg["json"]))
    currency = brand_cfg.get("currency", "NT$")

    st.markdown("---")
    st.markdown(
        '<div class="auto-update-info">🤖 <strong>自動更新</strong><br>資料每 4 小時由 GitHub Actions 自動抓取</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if data:
        products_all = data.get("products", [])
        all_cats = sorted(set(p.get("分類", "其他") for p in products_all))
        cat_counts = {c: 0 for c in all_cats}
        for p in products_all:
            cat_counts[p.get("分類", "其他")] = cat_counts.get(p.get("分類", "其他"), 0) + 1

        st.markdown("### 📂 商品分類")
        select_all = st.checkbox("全部分類", value=True)
        selected_cats = all_cats if select_all else [
            cat for cat in all_cats
            if st.checkbox(f"{cat}（{cat_counts.get(cat,0)}件）", value=False)
        ] or all_cats

        st.markdown("---")
        st.markdown(f"### 💰 價格範圍（{currency}）")
        prices_list = []
        for p in products_all:
            try:
                prices_list.append(int(p.get("現價", "0") or "0"))
            except Exception:
                pass
        if prices_list and min(prices_list) < max(prices_list):
            price_range = st.slider(f"現價（{currency}）", min(prices_list), max(prices_list),
                                    (min(prices_list), max(prices_list)), step=50)
        else:
            price_range = (0, 99999)

        st.markdown("---")
        st.markdown("### 🔃 排序方式")
        sort_option = st.selectbox("排序", ["預設排序", "現價：低→高", "現價：高→低", "折扣最多"],
                                   label_visibility="collapsed")
        st.markdown("---")
        scraped_at = data.get("scraped_at", "未知")
        st.markdown(f"<small style='color:#aaa'>最後更新：{scraped_at}</small>", unsafe_allow_html=True)
    else:
        sort_option = "預設排序"
        selected_cats = []
        price_range = (0, 99999)


# ── 主內容 ────────────────────────────────────────────────────
brand_color = brand_cfg.get("color", "#cc0000")
scraped_at_str = data.get("scraped_at", "") if data else "尚無資料"
st.markdown(
    f"""<div class='page-header' style='border-bottom-color:{brand_color}'>
<p class='page-title'>🛍️ {selected_brand}</p>
<p class='page-subtitle'>{scraped_at_str} ・ 每4小時自動更新</p>
</div>""",
    unsafe_allow_html=True,
)

if not data:
    st.markdown(
        "<div style='text-align:center;padding:60px;background:#fff;border-radius:12px'>"
        "<h3>📭 尚無資料</h3><p>資料將由 GitHub Actions 自動更新，請稍後再試</p></div>",
        unsafe_allow_html=True,
    )
else:
    products_all = data.get("products", [])

    # 篩選
    filtered = []
    for p in products_all:
        if p.get("分類", "其他") not in selected_cats:
            continue
        try:
            price = int(p.get("現價", "0") or "0")
        except Exception:
            price = 0
        if price > 0 and not (price_range[0] <= price <= price_range[1]):
            continue
        filtered.append(p)

    # 排序
    def get_price(p):
        try: return int(p.get("現價", "0") or "0")
        except Exception: return 0

    def get_discount(p):
        try:
            c, o = int(p.get("現價", "0") or "0"), int(p.get("原價", "0") or "0")
            return (o - c) / o if o > c > 0 else 0
        except Exception: return 0

    if sort_option == "現價：低→高":   filtered.sort(key=get_price)
    elif sort_option == "現價：高→低": filtered.sort(key=get_price, reverse=True)
    elif sort_option == "折扣最多":    filtered.sort(key=get_discount, reverse=True)

    st.markdown(
        f"<div class='stats-bar'>顯示 <strong>{len(filtered)}</strong> 件商品（共 {len(products_all)} 件）</div>",
        unsafe_allow_html=True,
    )

    if not filtered:
        st.info("😕 目前篩選條件下沒有符合的商品，請調整篩選條件。")
    else:
        COLS = 4
        badge_class = brand_cfg.get("badge_class", "brand-uniqlo")
        rows = [filtered[i: i + COLS] for i in range(0, len(filtered), COLS)]

        for row in rows:
            cols = st.columns(COLS, gap="small")
            for col, product in zip(cols, row):
                with col:
                    render_card(product, badge_class, currency, selected_brand)
