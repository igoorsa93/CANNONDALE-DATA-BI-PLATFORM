import requests
import re
import csv
from pathlib import Path

urls = [
    'https://www.cannondale.com/pt-br/bikes/road',
    'https://www.cannondale.com/pt-br/bikes/road/gravel',
    'https://www.cannondale.com/pt-br/bikes/mountain',
    'https://www.cannondale.com/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}
products = []

for url in urls:
    r = requests.get(url, headers=headers, timeout=15)
    print(f'\n=== {url.split("/")[-1]} === status={r.status_code} len={len(r.text)}')
    
    # Encontrar todas as tags <img>
    img_tags = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', r.text)
    bike_imgs = [i for i in img_tags if 'cloudfront' in i and '/bikes/' in i]
    print(f'  Imagens de bikes: {len(bike_imgs)}')
    
    # Encontrar nomes de produtos (ex: "Bad Boy 1", "Moterra Neo 1")
    # Os nomes geralmente aparecem em tags <h3> ou <a> próximos às imagens
    names = re.findall(r'<h[23][^>]*>\s*([^<]+)\s*</h[23]>', r.text)
    model_names = [n.strip() for n in names if n and not n.strip().startswith('#') and len(n) > 2]
    print(f'  Nomes encontrados: {model_names[:10]}...')
    
    # Relacionar imagens aos nomes (heurística: primeira imagem de bike perto de um nome de modelo)
    for i, img in enumerate(bike_imgs):
        if i < len(model_names):
            products.append({
                'modelo': model_names[i],
                'img_url': img,
                'url_produto': url
            })

out = Path('data/raw/produtos_novos.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['modelo', 'img_url', 'url_produto'])
    w.writeheader()
    w.writerows(products)

print(f'\nTotal de pares (modelo,img): {len(products)}')
print(f'Salvo em {out}')
