import requests
import re

urls = [
    'https://www.cannondale.com/pt-br/bikes/road',
    'https://www.cannondale.com/pt-br/bikes/road/gravel',
    'https://www.cannondale.com/pt-br/bikes/mountain',
    'https://www.cannondale.com/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}

for url in urls:
    r = requests.get(url, headers=headers, timeout=15)
    print(f'=== {url.split("/")[-1]} ===')
    # Extrair todos os links <a href="/pt-br/bikes/..."> com texto dentro
    matches = re.findall(r'<a[^>]+href="(/pt-br/bikes/[^"]+)"[^>]*>([^<]+)</a>', r.text)
    for href, text in matches[:20]:
        if len(text.strip()) > 2 and not text.strip().startswith('#'):
            print(f'  {text.strip()} -> {href}')
    print()
