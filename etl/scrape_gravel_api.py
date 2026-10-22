"""
Scrape Gravel category products using Typesense API (fast)
"""
import asyncio
import aiohttp
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

TYPESENSE_HOST = "th2gn1fbwadp739ep.a1.typesense.net"
TYPESENSE_COLLECTION = "prod-cd-products_v19"
TYPESENSE_API_KEY = "QaHJa8YV4lky2rkXT6BiA5JPCKeegOOy"

# Gravel category slugs
GRAVEL_SLUGS = [
    "road--gravel--topstone-carbon",
    "road--gravel--topstone-alloy", 
    "road--gravel--superx",
]

CLOUDFRONT_BASE = "https://d1mo5ln9tjltxq.cloudfront.net"

def build_widen_url(image_id, size="2400px@1x", fmt="jpg"):
    if not image_id:
        return ""
    return f"https://embed.widencdn.net/img/dorelrl/{image_id}/{size}/image.{fmt}?color=f8f8f8&q=90"

async def fetch_gravel_products(session, slug):
    """Fetch all products for a Gravel category slug"""
    url = f"https://{TYPESENSE_HOST}/collections/{TYPESENSE_COLLECTION}/documents/search"
    
    params = {
        "q": "*",
        "query_by": "model_name,model_code,consumer_name_3,salsify_id,skus,category,sub_category,segment,platform,brand,brake_types,frame_materials,wheel_sizes,sizes,description.pt,product_card_description.pt",
        "filter_by": f"country:=BR && has_price:=true && (product_type:=Bike && category_slugs:=[{slug}])",
        "per_page": "250",
        "page": "1",
        "include_fields": "salsify_id,relative_url,name,consumer_name_1,consumer_name_2,consumer_name_3,model_code,brand,platform,active_model_year,genders,category,sub_category,product_type,category_slugs,product_card_description,description,positioning_phrase,tags,badges,brake_types,frame_materials,suspensions,is_electric,available_on,variants"
    }
    
    headers = {
        "X-TYPESENSE-API-KEY": TYPESENSE_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                hits = data.get("hits", [])
                products = []
                
                for hit in hits:
                    doc = hit.get("document", {})
                    
                    # Build product URL
                    relative_url = doc.get("relative_url", "")
                    if relative_url.startswith("/"):
                        product_url = f"https://www.cannondale.com{relative_url}"
                    else:
                        product_url = f"https://www.cannondale.com/pt-br{relative_url}"
                    
                    # Extract price from variants
                    price = 0
                    variants = doc.get("variants", [])
                    if variants:
                        for v in variants:
                            if isinstance(v, dict):
                                # Try price_from first (in cents), then msrp_from
                                price_cents = v.get("price_from") or v.get("msrp_from")
                                if price_cents:
                                    try:
                                        price = float(price_cents) / 100.0
                                        break
                                    except:
                                        pass
                    
                    # Get model name
                    model_name = doc.get("consumer_name_3") or doc.get("consumer_name_2") or doc.get("consumer_name_1") or doc.get("name") or ""
                    
                    # Determine platform from slug
                    platform_map = {
                        "road--gravel--topstone-carbon": "Topstone Carbon",
                        "road--gravel--topstone-alloy": "Topstone Alloy",
                        "road--gravel--superx": "SuperX",
                    }
                    plataforma = platform_map.get(slug, "Gravel")
                    
                    # Extract specs
                    frame_materials = doc.get("frame_materials", [])
                    material = frame_materials[0] if frame_materials else ""
                    
                    suspensions = doc.get("suspensions", [])
                    suspension = suspensions[0] if suspensions else ""
                    
                    brake_types = doc.get("brake_types", [])
                    brakes = ", ".join(brake_types) if brake_types else ""
                    
                    wheel_sizes = doc.get("wheel_sizes", [])
                    wheels = ", ".join(wheel_sizes) if wheel_sizes else ""
                    
                    sizes = doc.get("sizes", [])
                    sizes_str = ", ".join(sizes) if sizes else ""
                    
                    # Colors from variants
                    colors = set()
                    for v in variants:
                        if isinstance(v, dict) and "color_swatch" in v:
                            colors.add(v["color_swatch"])
                    colors_str = ", ".join(sorted(colors))
                    
                    # Main image from variants
                    main_image = ""
                    if variants:
                        for v in variants:
                            if isinstance(v, dict) and "main_detail_image" in v and v["main_detail_image"]:
                                main_image = build_widen_url(v["main_detail_image"])
                                break
                    
                    # All images
                    all_images = []
                    if variants:
                        seen = set()
                        for v in variants:
                            if isinstance(v, dict):
                                for key in ["main_detail_image", "product_image_3q"]:
                                    img_id = v.get(key, "")
                                    if img_id and img_id not in seen:
                                        seen.add(img_id)
                                        all_images.append({
                                            "image_id": img_id,
                                            "url": build_widen_url(img_id),
                                            "color": v.get("color_swatch", ""),
                                            "size": v.get("size", "")
                                        })
                    
                    product = {
                        "id_produto": doc.get("salsify_id", ""),
                        "modelo": model_name,
                        "categoria": "Road",
                        "subcategoria": "Gravel",
                        "plataforma": plataforma,
                        "preco_site": price,
                        "moeda": "BRL",
                        "url_produto": product_url,
                        "url_imagem_principal": main_image,
                        "especificacoes": json.dumps({
                            "material_quadro": material,
                            "suspensao": suspension,
                            "freios": brakes,
                            "rodas": wheels,
                            "tamanhos": sizes_str,
                            "cores": colors_str,
                            "badges": ", ".join(doc.get("badges", [])),
                            "tags": ", ".join(doc.get("tags", [])),
                            "is_electric": doc.get("is_electric", False),
                        }, ensure_ascii=False),
                        "data_coleta": datetime.now().isoformat(),
                        "fonte": "Cannondale Oficial",
                        "tipo_dado": "OFICIAL",
                        "todas_imagens": json.dumps(all_images, ensure_ascii=False)
                    }
                    products.append(product)
                
                return products
            else:
                text = await resp.text()
                print(f"  Error {resp.status}: {text[:200]}")
                return []
    except Exception as e:
        print(f"  Exception: {e}")
        return []

async def main():
    print("=== CANNONDALE GRAVEL API SCRAPER ===")
    
    all_products = []
    
    async with aiohttp.ClientSession() as session:
        for slug in GRAVEL_SLUGS:
            print(f"Fetching: {slug}")
            products = await fetch_gravel_products(session, slug)
            print(f"  Found {len(products)} products")
            all_products.extend(products)
    
    # Save results
    RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = RAW_DIR / "gravel_products.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    # Also save as CSV
    import csv
    csv_file = RAW_DIR / "gravel_products.csv"
    if all_products:
        fieldnames = ["id_produto", "modelo", "categoria", "subcategoria", "plataforma", 
                     "preco_site", "moeda", "url_produto", "url_imagem_principal", 
                     "especificacoes", "data_coleta", "fonte", "tipo_dado", "todas_imagens"]
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in all_products:
                writer.writerow(p)
    
    print(f"\nTotal Gravel products: {len(all_products)}")
    for p in all_products:
        print(f"  {p['modelo']} | {p['plataforma']} | R$ {p['preco_site']:,.2f}")
    
    print(f"\nSaved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())