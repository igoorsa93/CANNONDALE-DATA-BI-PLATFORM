import os
import requests
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\igoor\OneDrive\Desktop\CANNONDALE DATA & BI PLATFORM")
CSV_PATH = ROOT / "data" / "processed" / "dim_imagens_validated.csv"
OUT_DIR = ROOT / "Imagens"

OUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(CSV_PATH)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

for _, row in df.iterrows():
    sku = str(row["id_produto_sku"])
    tipo = str(row["tipo_imagem"])
    url = str(row["url_imagem"])
    principal = bool(row["imagem_principal"])

    # Determina extensão
    ext = ".jpg"
    if ".ashx" in url:
        ext = ".jpg"  # ashx usually serves jpg
    elif ".png" in url:
        ext = ".png"
    elif ".webp" in url:
        ext = ".webp"

    filename = f"{sku}_{tipo}{ext}"
    filepath = OUT_DIR / filename

    if filepath.exists():
        print(f"SKIP (exists): {filename}")
        continue

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            print(f"OK: {filename} ({len(resp.content)} bytes)")
        else:
            print(f"ERRO {resp.status_code}: {filename} -> {url}")
    except Exception as e:
        print(f"FALHA: {filename} -> {e}")

print("\nConcluído.")
