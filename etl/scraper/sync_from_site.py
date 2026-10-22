import requests
import re
import csv
from pathlib import Path

RAW = Path('data/raw/cannabondale_produtos_raw.csv')
OUT = Path('data/raw/produtos_com_foto.csv')

headers = {'User-Agent': 'Mozilla/5.0'}
rows = []

with open(RAW, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

produtos_com_foto = []
for row in rows:
    url = row.get('url_produto', '')
    if not url or url.strip() == '':
        continue
    try:
        print(f'Fetch: {url.split("/")[-1]}')
        r = requests.get(url, headers=headers, timeout=10)
        # Extrair nome real do modelo (h1 ou título da página)
        title = ''
        m = re.search(r'<title>([^<]+)</title>', r.text)
        if m:
            title = m.group(1).replace(' | Cannondale', '').replace(' Cannondale', '').strip()
        # Extrair primeira imagem cloudfront de bike
        imgs = re.findall(r'(https://d1mo5ln9tjltxq\.cloudfront\.net/[^"\'\\]+\?[^"\'\\]+)', r.text)
        bike_img = ''
        for img in imgs:
            if 'bikes' in img and 'navigation' not in img:
                bike_img = img.replace('\\u0026', '&')
                break
        row['titulo_real'] = title
        row['img_url'] = bike_img
        produtos_com_foto.append(row)
    except Exception as e:
        print(f'Erro em {url}: {e}')
        row['titulo_real'] = ''
        row['img_url'] = ''
        produtos_com_foto.append(row)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    campos = list(row.keys()) if row else []
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(produtos_com_foto)

print(f'\nSalvos {len(produtos_com_foto)} em {OUT}')
