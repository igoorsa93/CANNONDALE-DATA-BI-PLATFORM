import requests
import re
import csv
from pathlib import Path

SITEMAP_PREFIX = 'https://a304077.sitemaphosting6.com/4356448/'
headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Pegar URLs de sitemap que são produtos (padrão /pt-br/bikes/...)
all_urls = []
for sm in ['sitemap1.xml', 'sitemap2.xml']:
    u = f'{SITEMAP_PREFIX}{sm}'
    try:
        r = requests.get(u, headers=headers, timeout=15)
        urls = re.findall(r'<loc>(https?://www\.cannondale\.com/pt-br/bikes/[^<]+)</loc>', r.text)
        all_urls.extend(urls)
    except Exception as e:
        print(e)

all_urls = list(set(all_urls))
print(f'Total de URLs de bikes no sitemap: {len(all_urls)}')

# 2. Para cada URL, pegar o HTML e extrair nome + imagem
results = []
for url in all_urls[:30]:  # limitar para não demorar demais
    try:
        r = requests.get(url, headers=headers, timeout=10)
        # Nome do produto
        m = re.search(r'<h1[^>]*>([^<]+)</h1>', r.text)
        name = m.group(1).strip() if m else 'Desconhecido'
        # Imagem principal da cloudfront em /bikes/
        img_match = re.search(r'(https://d1mo5ln9tjltxq\.cloudfront\.net/[^\"\']+?\?[^\"\']*)', r.text)
        if not img_match:
            img_match = re.search(r'(https://d1mo5ln9tjltxq\.cloudfront\.net/[^\"\']+?)', r.text)
        img = img_match.group(1).replace('\\u0026', '&') if img_match else ''
        results.append({'url': url, 'nome': name, 'img': img})
        print(f'  {name[:40]:<40} | {url.split("/")[-2]}')
    except Exception as e:
        print(f'  Erro em {url}: {e}')

out = Path('data/raw/modelos_extraidos.csv')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['url', 'nome', 'img'])
    w.writeheader()
    w.writerows(results)

print(f'\nSalvas {len(results)} linhas em {out}')
