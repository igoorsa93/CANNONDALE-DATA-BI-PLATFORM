import requests
import re
import json
from pathlib import Path

urls = [
    'https://www.cannondale.com/pt-br/bikes/road',
    'https://www.cannondale.com/pt-br/bikes/road/gravel',
    'https://www.cannondale.com/pt-br/bikes/mountain',
    'https://www.cannondale.com/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}

all_products = []

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f'\n=== {url.split("/")[-1]} ===')
        print(f'Status: {r.status_code} | Len: {len(r.text)}')

        # Busca todos os links de produtos
        product_links = re.findall(r'href="(/pt-br/bikes/[^"]+)"', r.text)
        # Remove duplicatas e pega apenas os links de produto individual
        products = list(set([l for l in product_links if '/bikes/' in l and not l.endswith('/bikes') and not l.endswith('/road') and not l.endswith('/gravel') and not l.endswith('/mountain') and not l.endswith('/electric')]))
        products.sort()

        print(f'Produtos encontrados: {len(products)}')
        for p in products[:10]:
            print(f'  {p}')

        all_products.extend(products)
    except Exception as e:
        print(f'Erro: {e}')

with open('product_links.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(all_products))

print(f'\nTotal de links de produtos: {len(all_products)}')
