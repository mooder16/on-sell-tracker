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
.main { background-color: #f8f8f8; }
.product-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 0;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.14);
}
.card-body { padding: 10px 12px 12px; }
.card-name {
    font-size: 13px;
    font-weight: 600;
    color: #222;
    margin-bottom: 8px;
    line-height: 1.4;
    min-height: 36px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.card-price { margin-bottom: 10px; line-height: 1.6; }
.price-current { font-size: 20px; font-weight: 800; color: #e00; }
.price-currency { font-size: 13px; font-weight: 600; color: #e00; }
.price-original {
    font-size: 13px; color: #999;
    text-decoration: line-through;
    margin-left: 4px;
}
.price-discount {
    display: inline-block;
    background: #e00; color: #fff;
    font-size: 11px; font-weight: 700;
    padding: 2px 6px; border-radius: 4px; margin-left: 4px;
    vertical-align: middle;
}
.limit-badge {
    display: inline-block;
    background: #ff6600; color: #fff;
    font-size: 11px; font-weight: 700;
    padding: 3px 8px; border-radius: 4px;
    margin-bottom: 6px;
}
.btn-buy {
    display: block; text-align: center;
    background: #222; color: #fff !important;
    text-decoration: none !important;
    padding: 9px 0; border-radius: 6px;
    font-size: 13px; font-weight: 600;
    transition: background 0.2s;
}
.btn-buy:hover { background: #e00; color: #fff !important; }
.category-badge {
    display: inline-block;
    background: #f0f0f0; color: #555;
    font-size: 11px; padding: 2px 8px;
    border-radius: 20px; margin-bottom: 6px;
}
.brand-badge {
    display: inline-block;
    font-size: 10px; padding: 2px 6px;
    border-radius: 4px; margin-bottom: 4px;
    font-weight: 700; margin-right: 4px;
}
.brand-uniqlo { background: #e00; color: #fff; }
.brand-limited { background: #ff6600; color: #fff; }
.brand-momo { background: #e91e8c; color: #fff; }
.brand-muji { background: #8b7355; color: #fff; }
.page-header {
    padding: 10px 0 20px;
    border-bottom: 2px solid #e00;
    margin-bottom: 24px;
}
.page-title { font-size: 28px; font-weight: 800; color: #222; margin: 0; }
.page-subtitle { font-size: 14px; color: #888; margin-top: 4px; }
.stats-bar {
    background: #fff; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 14px; color: #555;
}
.no-data-box {
    text-align: center; padding: 60px 20px;
    background: #fff; border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.auto-update-info {
    background: #f0f7ff;
    border: 1px solid #c0d8f0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #4a7aaa;
    margin-bottom: 8px;
}
/* 讓 st.image 在卡片內填滿 */
[data-testid="stImage"] img {
    border-radius: 0 !important;
    width: 100% !important;
    aspect-ratio: 1/1;
    object-fit: cover;
}
</style>
""", unsafe_allow_html=True)

# ── 品牌設定 ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

BRANDS = {
    "UNIQLO 日本特賣": {
        "json": BASE_DIR / "uniqlo_jp_deals.json",
        "badge_class": "brand-uniqlo",
        "color": "#e00",
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
        "color": "#e00",
        "currency": "NT$",
    },
}


@st.cache_data(ttl=3600)
def load_data(json_path: str):
    p = Path(json_path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ── 側邊欄 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ 特價商品追蹤")
    st.markdown("---")

    st.markdown("### 🏪 選擇品牌")
    selected_brand = st.radio(
        "品牌",
        list(BRANDS.keys()),
        label_visibility="collapsed",
    )

    brand_cfg = BRANDS[selected_brand]
    data = load_data(str(brand_cfg["json"]))
    currency = brand_cfg.get("currency", "NT$")

    st.markdown("---")

    # 自動更新說明（取代原本的更新按鈕）
    st.markdown(
        """
        <div class="auto-update-info">
            🤖 <strong>自動更新</strong><br>
            資料每 4 小時由 GitHub Actions 自動抓取更新
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if data:
        products_all = data.get("products", [])

        st.markdown("### 📂 商品分類")
        all_cats = sorted(set(p.get("分類", "其他") for p in products_all))
        cat_counts = {}
        for p in products_all:
            c = p.get("分類", "其他")
            cat_counts[c] = cat_counts.get(c, 0) + 1

        select_all = st.checkbox("全部分類", value=True)
        selected_cats = []
        if not select_all:
            for cat in all_cats:
                if st.checkbox(f"{cat}（{cat_counts.get(cat, 0)}件）", value=False):
                    selected_cats.append(cat)
            if not selected_cats:
                selected_cats = all_cats
        else:
            selected_cats = all_cats

        st.markdown("---")

        st.markdown(f"### 💰 價格範圍（{currency}）")
        prices_list = []
        for p in products_all:
            try:
                prices_list.append(int(p.get("現價", "0") or "0"))
            except:
                pass
        if prices_list:
            min_p, max_p = min(prices_list), max(prices_list)
            if min_p < max_p:
                price_range = st.slider(
                    f"現價（{currency}）", min_p, max_p, (min_p, max_p), step=50
                )
            else:
                price_range = (min_p, max_p)
        else:
            price_range = (0, 99999)

        st.markdown("---")

        st.markdown("### 🔃 排序方式")
        sort_option = st.selectbox(
            "排序",
            ["預設排序", "現價：低→高", "現價：高→低", "折扣最多"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        scraped_at = data.get("scraped_at", "未知")
        st.markdown(
            f"<small style='color:#aaa'>最後更新：{scraped_at}</small>",
            unsafe_allow_html=True,
        )
    else:
        sort_option = "預設排序"
        selected_cats = []
        price_range = (0, 99999)


# ── 主內容 ────────────────────────────────────────────────────
brand_color = brand_cfg.get("color", "#e00")
st.markdown(
    f"""
<div class='page-header' style='border-bottom-color:{brand_color}'>
    <p class='page-title'>🛍️ {selected_brand}</p>
    <p class='page-subtitle'>{data.get('scraped_at', '') if data else '尚無資料'} ・ 每4小時自動更新</p>
</div>
""",
    unsafe_allow_html=True,
)

if not data:
    st.markdown(
        """
    <div class='no-data-box'>
        <h3>📭 尚無資料</h3>
        <p>資料將由 GitHub Actions 自動更新，請稍後再試</p>
    </div>
    """,
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
        except:
            price = 0
        if price > 0 and not (price_range[0] <= price <= price_range[1]):
            continue
        filtered.append(p)

    # 排序
    def get_price(p):
        try:
            return int(p.get("現價", "0") or "0")
        except:
            return 0

    def get_discount(p):
        try:
            cur = int(p.get("現價", "0") or "0")
            ori = int(p.get("原價", "0") or "0")
            return (ori - cur) / ori if ori > cur > 0 else 0
        except:
            return 0

    if sort_option == "現價：低→高":
        filtered.sort(key=get_price)
    elif sort_option == "現價：高→低":
        filtered.sort(key=get_price, reverse=True)
    elif sort_option == "折扣最多":
        filtered.sort(key=get_discount, reverse=True)

    st.markdown(
        f"""
    <div class='stats-bar'>
        顯示 <strong>{len(filtered)}</strong> 件商品（共 {len(products_all)} 件）
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not filtered:
        st.info("😕 目前篩選條件下沒有符合的商品，請調整篩選條件。")
    else:
        COLS = 4
        rows = [filtered[i : i + COLS] for i in range(0, len(filtered), COLS)]
        badge_class = brand_cfg.get("badge_class", "brand-uniqlo")

        for row in rows:
            cols = st.columns(COLS)
            for col, product in zip(cols, row):
                with col:
                    name = product.get("商品名稱", "")
                    current = product.get("現價", "")
                    original = product.get("原價", "")
                    image_url = product.get("圖片網址", "")
                    product_url = product.get("商品連結", "")
                    category = product.get("分類", "其他")
                    brand = product.get("品牌", selected_brand)

                    # 折扣計算
                    discount_html = ""
                    try:
                        cur_int = int(current)
                        ori_int = int(original)
                        if ori_int > cur_int > 0:
                            pct = round((1 - cur_int / ori_int) * 100)
                            discount_html = f'<span class="price-discount">-{pct}%</span>'
                    except:
                        pass

                    # 原價（有折扣才顯示）
                    orig_html = ""
                    if original and original != current:
                        orig_html = f'<span class="price-original">{currency}{original}</span>'

                    # 現價
                    price_display = (
                        f'<span class="price-currency">{currency}</span>'
                        f'<span class="price-current">{current}</span>'
                        if current
                        else '<span style="color:#999">價格未知</span>'
                    )

                    # 截止日期（期間限定特價）
                    limit_until = product.get("截止日期", "")
                    limit_html = (
                        f'<div><span class="limit-badge">⏰ {limit_until}期間限定</span></div>'
                        if limit_until
                        else ""
                    )

                    # 購買按鈕
                    btn_html = (
                        f'<a href="{product_url}" target="_blank" class="btn-buy">前往購買 →</a>'
                        if product_url
                        else '<span style="color:#ccc;font-size:12px;">無連結</span>'
                    )

                    # 卡片上半（圖片）
                    st.markdown(
                        '<div class="product-card">',
                        unsafe_allow_html=True,
                    )

                    # 圖片：直接用圖片 URL
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    else:
                        st.markdown(
                            '<div style="text-align:center;padding:30px;font-size:36px;background:#f5f5f5;">👗</div>',
                            unsafe_allow_html=True,
                        )

                    # 卡片下半（文字）
                    st.markdown(
                        f"""
<div class="card-body">
  <span class="brand-badge {badge_class}">{brand}</span>
  <span class="category-badge">{category}</span>
  {limit_html}
  <div class="card-name">{name}</div>
  <div class="card-price">
    {price_display}
    {orig_html}
    {discount_html}
  </div>
  {btn_html}
</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
