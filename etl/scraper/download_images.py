"""
Download all product images from variants
"""
import asyncio
import aiohttp
import aiofiles
import json
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
IMAGES_DIR = ROOT / "Imagens"

for d in [IMAGES_DIR / "road", IMAGES_DIR / "gravel", IMAGES_DIR / "mountain", 
          IMAGES_DIR / "electric", IMAGES_DIR / "active", IMAGES_DIR / "kids"]:
    d.mkdir(parents=True, exist_ok=True)

async def download_image(session, url, filepath):
    """Download a single image"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                content = await resp.read()
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                return True, len(content)
            else:
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

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
    print("=== CANNONDALE IMAGE DOWNLOADER ===")
    
    # Load products
    json_file = RAW_DIR / "produtos_reais_api.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    
    # Collect all images from variants
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
                    "url": img["url"],
                    "color": img.get("color", ""),
                    "size": img.get("size", "")
                })
        except:
            # Fallback to main image
            if p.get("url_imagem_principal"):
                all_images.append({
                    "produto_id": p["id_produto"],
                    "produto_modelo": p["modelo"],
                    "produto_categoria": p["categoria"],
                    "image_id": "main",
                    "url": p["url_imagem_principal"],
                    "color": "",
                    "size": ""
                })
    
    print(f"Total images to download: {len(all_images)}")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_images = []
    for img in all_images:
        if img["url"] not in seen_urls:
            seen_urls.add(img["url"])
            unique_images.append(img)
    
    print(f"Unique images: {len(unique_images)}")
    
    # Download images
    image_catalog = []
    connector = aiohttp.TCPConnector(limit=10)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i, img in enumerate(unique_images):
            print(f"[{i+1}/{len(unique_images)}] {img['produto_modelo']} - {img['image_id']}")
            
            # Determine folder and filename
            folder = get_category_folder(img["produto_categoria"])
            modelo_safe = img["produto_modelo"].replace("/", "-").replace(" ", "_")
            
            # Create filename
            ext = ".jpg"
            filename = f"{modelo_safe}_{img['image_id']}{ext}"
            filepath = IMAGES_DIR / folder / filename
            
            # Download
            success, result = await download_image(session, img["url"], filepath)
            
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
                    "url_imagem": img["url"],
                    "tipo_imagem": "Principal" if img["image_id"] == "main" or i == 0 else "Detalhe",
                    "imagem_principal": i == 0,
                    "nome_arquivo": filename,
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
                    "url_imagem": img["url"],
                    "tipo_imagem": "Principal" if img["image_id"] == "main" or i == 0 else "Detalhe",
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
    
    print(f"\n✅ Image catalog saved to {csv_file}")
    
    # Save JSON
    json_file = RAW_DIR / "catalogo_imagens.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(image_catalog, f, ensure_ascii=False, indent=2)
    print(f"✅ Image catalog JSON saved to {json_file}")
    
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