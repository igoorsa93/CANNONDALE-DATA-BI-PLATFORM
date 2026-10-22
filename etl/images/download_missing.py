import requests
import re
import os
from pathlib import Path

ROOT = Path(r"C:\Users\igoor\OneDrive\Desktop\CANNONDALE DATA & BI PLATFORM")
OUT_DIR = ROOT / "Imagens"
OUT_DIR.mkdir(exist_ok=True)

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
    r = requests.get(url, headers=headers, timeout=15)
    # Filtra imagens de bike (exclui navigation, banners, etc)
    all_imgs = re.findall(r'https://d1mo5ln9tjltxq\.cloudfront\.net/[^"\']+\.ashx(?:\?[^"\']*)?', r.text)
    # Pega só as de /bikes/
    bike_imgs = [u for u in all_imgs if '/bikes/' in u and 'navigation' not in u]
    if not bike_imgs:
        # Fallback: pega qualquer uma da cloudfront
        bike_imgs = all_imgs[:1]
    if bike_imgs:
        img_url = bike_imgs[0]
        # Fix: garante URL bem formada
        if '?' in img_url:
            img_url = img_url.split('?')[0]
        ext = '.jpg'
        filename = f"{sku}_principal{ext}"
        filepath = OUT_DIR / filename
        try:
            img_r = requests.get(img_url, headers=headers, timeout=15)
            if img_r.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(img_r.content)
                print(f"OK: {filename} ({len(img_r.content)} bytes)")
            else:
                print(f"ERRO {img_r.status_code}: {filename}")
        except Exception as e:
            print(f"FALHA: {filename} -> {e}")
    else:
        print(f"NÃO ENCONTRADO: {sku}")
