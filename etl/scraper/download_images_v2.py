"""
Download all product images from Widen CDN using image IDs from API
"""
import asyncio
import aiohttp
import aiofiles
import json
import csv
import hashlib
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
IMAGES_DIR = ROOT / "Imagens"

for d in [IMAGES_DIR / "road", IMAGES_DIR / "gravel", IMAGES_DIR / "mountain", 
          IMAGES_DIR / "electric", IMAGES_DIR / "active", IMAGES_DIR / "kids"]:
    d.mkdir(parents=True, exist_ok=True)

WIDEN_BASE = "https://embed.widencdn.net/img/dorelrl"

async def download_image(session, url, filepath):
    """Download a single image"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                content = await resp.read()
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                return True, len(content)
            else:
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

def build_widen_url(image_id, size="2400px@1x", fmt="jpg"):
    """Build Widen CDN URL from image ID"""
    if not image_id:
        return ""
    # Use a generic filename pattern - the actual filename varies but we can use a generic one
    return f"{WIDEN_BASE}/{image_id}/{size}/image.{fmt}?color=f8f8f8&q=90"

def get_category_folder(categoria):
    """Map category to folder"""
    cat = categoria.lower()
    if cat == "road":
        return "road"
    elif cat == "gravel":
        return "gravel"
    elif cat == "mountain":
        return "mountain"
    elif cat == "electric":
        return "electric"
    elif cat == "active":
        return "active"
    elif cat == "kids":
        return "kids"
    else:
        return "outros"

async def main():
    print("=== CANNONDALE IMAGE DOWNLOADER (Widen CDN) ===")
    
    # Load products
    json_file = RAW_DIR / "produtos_reais_api.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    
    # Collect all unique image IDs from variants
    all_images = []
    for p in products:
        try:
            imagens = json.loads(p.get("todas_imagens", "[]"))
            for img in imagens:
                all_images.append({
                    "produto_id": p["id_produto"],
                    "produto_modelo": p["modelo"],
                    "produto_categoria": p["categoria"],
                    "image_id": img["image_id"],
                    "color": img.get("color", ""),
                    "size": img.get("size", "")
                })
        except:
            pass
    
    print(f"Total image IDs collected: {len(all_images)}")
    
    # Deduplicate by image_id
    seen_ids = set()
    unique_images = []
    for img in all_images:
        if img["image_id"] not in seen_ids:
            seen_ids.add(img["image_id"])
            unique_images.append(img)
    
    print(f"Unique image IDs: {len(unique_images)}")
    
    # Download images
    image_catalog = []
    connector = aiohttp.TCPConnector(limit=5)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i, img in enumerate(unique_images):
            print(f"[{i+1}/{len(unique_images)}] {img['produto_modelo']} - {img['image_id']}")
            
            # Build Widen URL - try jpg first at 2400px
            url = build_widen_url(img["image_id"], "2400px@1x", "jpg")
            
            # Determine folder and filename
            folder = get_category_folder(img["produto_categoria"])
            modelo_safe = re.sub(r'[^\w\-]', '_', img["produto_modelo"])
            filename = f"{modelo_safe}_{img['image_id']}.jpg"
            filepath = IMAGES_DIR / folder / filename
            
            # Download
            success, result = await download_image(session, url, filepath)
            
            if not success:
                # Try webp format
                url = build_widen_url(img["image_id"], "2400px@1x", "webp")
                filepath = filepath.with_suffix(".webp")
                success, result = await download_image(session, url, filepath)
            
            if not success:
                # Try 2560px size
                url = build_widen_url(img["image_id"], "2560px@1x", "jpg")
                filepath = filepath.with_suffix(".jpg")
                success, result = await download_image(session, url, filepath)
            
            if success:
                # Calculate hash
                async with aiofiles.open(filepath, 'rb') as f:
                    content = await f.read()
                    file_hash = hashlib.md5(content).hexdigest()
                
                print(f"  OK - {result} bytes - {file_hash[:8]}")
                
                image_catalog.append({
                    "id_imagem": f"img_{len(image_catalog)+1:06d}",
                    "id_produto": img["produto_id"],
                    "modelo": img["produto_modelo"],
                    "categoria": img["produto_categoria"],
                    "url_produto": next((p["url_produto"] for p in products if p["id_produto"] == img["produto_id"]), ""),
                    "url_imagem": url,
                    "tipo_imagem": "Principal" if i == 0 else "Detalhe",
                    "imagem_principal": i == 0,
                    "nome_arquivo": filepath.name,
                    "caminho_local": str(filepath),
                    "hash_md5": file_hash,
                    "tamanho_bytes": result,
                    "data_download": datetime.now().isoformat(),
                    "status": "OK"
                })
            else:
                print(f"  FAILED - {result}")
                image_catalog.append({
                    "id_imagem": f"img_{len(image_catalog)+1:06d}",
                    "id_produto": img["produto_id"],
                    "modelo": img["produto_modelo"],
                    "categoria": img["produto_categoria"],
                    "url_produto": next((p["url_produto"] for p in products if p["id_produto"] == img["produto_id"]), ""),
                    "url_imagem": url,
                    "tipo_imagem": "Principal" if i == 0 else "Detalhe",
                    "imagem_principal": i == 0,
                    "nome_arquivo": filename,
                    "caminho_local": "",
                    "hash_md5": "",
                    "tamanho_bytes": 0,
                    "data_download": datetime.now().isoformat(),
                    "status": f"FAILED: {result}"
                })
    
    # Save image catalog
    csv_file = RAW_DIR / "catalogo_imagens.csv"
    fieldnames = [
        "id_imagem", "id_produto", "modelo", "categoria", "url_produto",
        "url_imagem", "tipo_imagem", "imagem_principal", "nome_arquivo",
        "caminho_local", "hash_md5", "tamanho_bytes", "data_download", "status"
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for img in image_catalog:
            writer.writerow(img)
    
    print(f"Image catalog saved to {csv_file}")
    
    # Save JSON
    json_file = RAW_DIR / "catalogo_imagens.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(image_catalog, f, ensure_ascii=False, indent=2)
    print(f"Image catalog JSON saved to {json_file}")
    
    # Summary
    ok_count = sum(1 for i in image_catalog if i["status"] == "OK")
    fail_count = sum(1 for i in image_catalog if i["status"] != "OK")
    total_size = sum(i["tamanho_bytes"] for i in image_catalog if i["status"] == "OK")
    
    print(f"\n=== DOWNLOAD SUMMARY ===")
    print(f"  Successful: {ok_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total size: {total_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    asyncio.run(main())