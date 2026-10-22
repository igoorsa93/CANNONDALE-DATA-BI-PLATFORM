import requests
import re
import csv
from pathlib import Path

BASE = 'https://www.cannondale.com'
urls = [
    f'{BASE}/pt-br/bikes/road',
    f'{BASE}/pt-br/bikes/road/gravel',
    f'{BASE}/pt-br/bikes/mountain',
    f'{BASE}/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}
products = []

for url in urls:
    r = requests.get(url, headers=headers, timeout=15)
    # Links de produto são padrões /pt-br/bikes/.../nome-do-modelo
    pattern = r'href="(/pt-br/bikes/[^"]+)"'
    links = set(re.findall(pattern, r.text))
    # Filtrar apenas links que parecem ser produto individual (contêm nome de bike)
    bike_links = [l for l in links if any(x in l for x in ['supersix', 'caad', 'caad', 'topstone', 'superx', 'scalpel', 'moterra', 'trail', 'bad', 'quick', 'treadwell', 'jekyll', 'habit', 'dave', 'f-si', 'superslice', 'sims', 'synth', 'overdrive', 'f-series', 'b-series', 'r-series', 'twenty', 'Jekyll', 'Jekyll', ' Habit', ' Habit', 'Moterra', 'Trail', 'Quick', 'Treadwell', 'SuperFlat', 'Bad', 'CAAD', 'Capo', 'Slice', 'Synapse', 'SuperSix', 'Science', 'Flash', 'SystemSix', 'Synapse'])]
    # Se não encontrou, pega todos os links de bike
    if not bike_links:
        bike_links = [l for l in links if '/bikes/' in l and '/bikes/road' not in l and '/bikes/mountain' not in l and '/bikes/electric' not in l]
    print(f'{url.split("/")[-1]}: {len(bike_links)} candidatos')
    for link in list(bike_links)[:20]:
        products.append(link)

# Remove duplicates
products = list(set(products))
print(f'\nTotal candidatos: {len(products)}')

# Para cada candidato, abrir a página e extrair nome + imagem principal
results = []
for link in products[:30]:  # limitar para teste
    full_url = BASE + link
    try:
        r = requests.get(full_url, headers=headers, timeout=10)
        # Nome do produto geralmente está em <h1>
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', r.text)
        name = name_match.group(1).strip() if name_match else 'Unknown'
        # Imagem principal do produto
        img_match = re.search(r'(https://d1mo5ln9tjltxq\.cloudfront\.net/[^"]+?/bikes/[^"]+?\.ashx)', r.text)
        img = img_match.group(1) if img_match else ''
        results.append({
            'url': full_url,
            'nome': name,
            'img': img
        })
        print(f'  {name} -> {img[:80]}')
    except Exception as e:
        print(f'  Erro em {link}: {e}')

out = Path('data/raw/produtos_reais.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['url', 'nome', 'img'])
    w.writeheader()
    w.writerows(results)

print(f'\nSalvos {len(results)} produtos em {out}')