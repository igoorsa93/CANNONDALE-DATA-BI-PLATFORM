import requests
import re
import csv
from pathlib import Path

SITEMAP_BASE = 'https://a304077.sitemaphosting6.com/4356448/'
headers = {'User-Agent': 'Mozilla/5.0'}

all_urls = []
for sm in ['sitemap1.xml', 'sitemap2.xml']:
    try:
        r = requests.get(SITEMAP_BASE + sm, headers=headers, timeout=10)
        urls = re.findall(r'<loc>(https?://www\.cannondale\.com/pt-br/bikes/[^<]+)</loc>', r.text)
        all_urls.extend(urls)
    except Exception as e:
        print(f'Erro {sm}: {e}')

all_urls = sorted(set(all_urls))
print(f'URLs totais: {len(all_urls)}')
# limitar a 15 para teste
test_urls = all_urls[:15]
products = []
for url in test_urls:
    try:
        r = requests.get(url, headers=headers, timeout=8)
        title_match = re.search(r'<title>([^<]+)</title>', r.text)
        title = title_match.group(1).replace(' | Cannondale', '').strip() if title_match else ''
        name = title.split('|')[0].strip() if title else ''
        if len(name) < 3:
            name = url.split('/')[-2] if len(url.split('/')) > 2 else url.split('/')[-1]
        imgs = re.findall(r'(https://d1mo5ln9tjltxq\.cloudfront\.net/[^"\'\\]+\?[^"\'\\]*)', r.text)
        bike_img = ''
        for img in imgs:
            if '/bikes/' in img and 'navigation' not in img and 'banner' not in img:
                bike_img = img.replace('\\u0026', '&')
                break
        if not bike_img:
            for img in imgs:
                if '/my' in img and 'navigation' not in img:
                    bike_img = img.replace('\\u0026', '&')
                    break
        products.append({'url': url, 'nome': name, 'img': bike_img})
        print(f'{name[:30]:<30} | {bike_img[:60]}')
    except Exception as e:
        print(f'Erro {url}: {e}')

out = Path('data/raw/produtos_reais_teste.csv')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['url', 'nome', 'img'])
    w.writeheader()
    w.writerows(products)

print(f'\nSalvos {len(products)} produtos em {out}')
