import requests
import re
import csv
from pathlib import Path

# URLs de categorias para extrair nomes reais
urls = [
    'https://www.cannondale.com/pt-br/bikes/road',
    'https://www.cannondale.com/pt-br/bikes/road/gravel',
    'https://www.cannondale.com/pt-br/bikes/mountain',
    'https://www.cannondale.com/pt-br/bikes/electric',
]

headers = {'User-Agent': 'Mozilla/5.0'}
models = []

for url in urls:
    r = requests.get(url, headers=headers, timeout=15)
    # Títulos de produtos geralmente em <h3> ou <a> com classe 'product-name'
    # Vamos extrair todos os textos que pareçam nomes de bikes
    # Também buscar por padrões como "NomeBike X" com números
    texts = re.findall(r'<h[23][^>]*>([^<]+)</h[23]>', r.text)
    for t in texts:
        t = t.strip()
        # Filtrar nomes que parecem modelo de bike (contêm letras maiúsculas iniciais e números)
        if len(t) > 2 and not t.startswith('#') and any(c.isdigit() for c in t):
            models.append(t)
    # Também extrair de meta tags og:title? Não.
    # Tentar pegar só os nomes dos modelos da página de forma mais simples
    # Procurar por strings conhecidas em h3
    print(f'{url.split("/")[-1]}: {len(models)} nomes de marcas/modelos com número')
    print(models[:5])

# Remove duplicates preservando ordem
seen = set()
unique = []
for m in models:
    if m not in seen:
        seen.add(m)
        unique.append(m)

out = Path('data/raw/modelos_nome_extraidos.txt')
with open(out, 'w', encoding='utf-8') as f:
    for m in unique:
        f.write(m + '\n')

print(f'\nTotal de modelos com número: {len(unique)}')
print(f'Salvos em {out}')
