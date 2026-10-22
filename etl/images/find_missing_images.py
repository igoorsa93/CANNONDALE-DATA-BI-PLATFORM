import requests
import re

urls = {
    'BADBOY-2026-001': 'https://www.cannondale.com/pt-br/bikes/active/urban/bad-boy',
    'CAAD14-2026-001': 'https://www.cannondale.com/pt-br/bikes/road/race/caad14',
    'QUICK-2026-001': 'https://www.cannondale.com/pt-br/bikes/active/fitness/quick',
    'SCALPEL-HT-2026-001': 'https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel-ht',
    'CAD014-2026-002': 'https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-2/2026',
    'TREADWELL-2026-001': 'https://www.cannondale.com/pt-br/bikes/active/fitness/treadwell',
}

headers = {'User-Agent': 'Mozilla/5.0'}

for sku, url in urls.items():
    r = requests.get(url, headers=headers, timeout=10)
    imgs = re.findall(r'https://d1mo5ln9tjltxq.cloudfront.net[^"\']+\.ashx', r.text)
    print(f'{sku}: {len(imgs)} imgs encontradas')
    for img in imgs[:2]:
        print(f'  {img[:100]}')
