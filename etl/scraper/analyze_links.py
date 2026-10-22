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
    print(f'=== {url} ===')
    # Extrair todo texto entre <a ...>...</a> que contenha /bikes/
    blocks = re.findall(r'<a[^>]+>(.*?)</a>', r.text, re.DOTALL)
    for b in blocks:
        # Remove tags internas
        text = re.sub(r'<.*?>', '', b)
        text = text.strip()
        if text and len(text) > 2 and 'Cannondale' not in text and 'Veja Todas' not in text and 'Details' not in text:
            # Escrever texto com url
            href_match = re.search(r'href="([^"]+)"', b)
            href = href_match.group(1) if href_match else ''
            if '/pt-br/bikes/' in href:
                print(f'  {text[:60]} -> {href[:60]}')
