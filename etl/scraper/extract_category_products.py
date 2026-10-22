import requests
import re
import csv
from pathlib import Path

# URLs de categorias fornecidas pelo usuário
CATEGORY_URLS = [
    'https://www.cannondale.com/pt-br/bikes/road',
    'https://www.cannondale.com/pt-br/bikes/road/gravel',
    'https://www.cannondale.com/pt-br/bikes/mountain',
    'https://www.cannondale.com/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}
all_products = []

for url in CATEGORY_URLS:
    r = requests.get(url, headers=headers, timeout=15)
    # Extrair links de produtos dentro da página de categoria
    links = re.findall(r'href="(/pt-br/bikes/[^"]+/[^"]+/)"', r.text)
    # Também tentar href simples
    links2 = re.findall(r'href="(/pt-br/bikes/[^"]+)"', r.text)
    links = list(set(links + links2))
    print(f'{url.split("/")[-1]}: {len(links)} links')
    for link in links:
        parts = link.strip('/').split('/')
        if len(parts) >= 4:
            modelo = parts[-2].replace('-', ' ').title()
            full_url = 'https://www.cannondale.com' + link
            all_products.append({'url': full_url, 'modelo': modelo})

# Salvar CSV bruto
out = Path('data/raw/produtos_categorias.csv')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['url', 'modelo'])
    w.writeheader()
    w.writerows(all_products)

print(f'Total: {len(all_products)} produtos')
for p in all_products[:10]:
    print(p)
