import json
with open('daily_deals.json', encoding='utf-8') as f:
    data = json.load(f)
products = data.get('products', [])
print(f'共 {len(products)} 件商品')
print('前5件商品連結：')
for p in products[:5]:
    name = p.get('商品名稱', '')[:25]
    link = p.get('商品連結', '')
    print(f'  {name}')
    print(f'  -> {link}')
    print()
