"""
Fetch ALL products using the correct category slugs
"""
import asyncio
import aiohttp
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for d in [RAW_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TYPESENSE_HOST = "th2gn1fbwadp739ep.a1.typesense.net"
TYPESENSE_COLLECTION = "prod-cd-products_v19"
TYPESENSE_API_KEY = "QaHJa8YV4lky2rkXT6BiA5JPCKeegOOy"

# Deep category slugs that actually have products (from discovery)
DEEP_SLUGS = [
    "road--race--supersix-evo",
    "road--gravel--topstone-carbon",
    "road--gravel--topstone-alloy",
    "road--gravel--superx",
    "mountain--cross-country--scalpel",
    "mountain--cross-country--scalpel-ht",
    "mountain--trail-bikes--trail",
    "electric--e-mountain--moterra-neo",
    "electric--e-mountain--moterra-neo-lt",
    "electric--e-mountain--moterra-sl",
]

# Mapping for display
SLUG_META = {
    "road--race--supersix-evo": {"categoria": "Road", "subcategoria": "Race", "plataforma": "SuperSix EVO"},
    "road--gravel--topstone-carbon": {"categoria": "Road", "subcategoria": "Gravel", "plataforma": "Topstone Carbon"},
    "road--gravel--topstone-alloy": {"categoria": "Road", "subcategoria": "Gravel", "plataforma": "Topstone Alloy"},
    "road--gravel--superx": {"categoria": "Road", "subcategoria": "Gravel", "plataforma": "SuperX"},
    "mountain--cross-country--scalpel": {"categoria": "Mountain", "subcategoria": "Cross Country", "plataforma": "Scalpel"},
    "mountain--cross-country--scalpel-ht": {"categoria": "Mountain", "subcategoria": "Cross Country", "plataforma": "Scalpel HT"},
    "mountain--trail-bikes--trail": {"categoria": "Mountain", "subcategoria": "Trail", "plataforma": "Trail"},
    "electric--e-mountain--moterra-neo": {"categoria": "Electric", "subcategoria": "E-MTB", "plataforma": "Moterra Neo"},
    "electric--e-mountain--moterra-neo-lt": {"categoria": "Electric", "subcategoria": "E-MTB", "plataforma": "Moterra Neo LT"},
    "electric--e-mountain--moterra-sl": {"categoria": "Electric", "subcategoria": "E-MTB", "plataforma": "Moterra SL"},
}

async def fetch_products_for_slug(session, slug):
    """Fetch all products for a specific deep category slug"""
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
                
                meta = SLUG_META.get(slug, {"categoria": "", "subcategoria": "", "plataforma": ""})
                
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
                            if isinstance(v, dict) and "price" in v:
                                try:
                                    price = float(v["price"])
                                    break
                                except:
                                    pass
                    
                    # Get model name
                    model_name = doc.get("consumer_name_3") or doc.get("consumer_name_2") or doc.get("consumer_name_1") or doc.get("name") or ""
                    
                    # Determine year
                    year = doc.get("active_model_year", 2026)
                    try:
                        year = int(year) if year else 2026
                    except:
                        year = 2026
                    
                    # Extract SKU/model code
                    sku = doc.get("salsify_id", "")
                    model_code = doc.get("model_code", "") if "model_code" in doc else sku
                    
                    # Frame material
                    frame_materials = doc.get("frame_materials", [])
                    material = frame_materials[0] if frame_materials else ""
                    
                    # Suspension
                    suspensions = doc.get("suspensions", [])
                    suspension = suspensions[0] if suspensions else ""
                    
                    # Brake types
                    brake_types = doc.get("brake_types", [])
                    brakes = ", ".join(brake_types) if brake_types else ""
                    
                    # Wheel sizes
                    wheel_sizes = doc.get("wheel_sizes", [])
                    wheels = ", ".join(wheel_sizes) if wheel_sizes else ""
                    
                    # Sizes available
                    sizes = doc.get("sizes", [])
                    sizes_str = ", ".join(sizes) if sizes else ""
                    
                    # Badges/tags
                    badges = doc.get("badges", [])
                    tags = doc.get("tags", [])
                    badge_str = ", ".join(badges) if badges else ""
                    tag_str = ", ".join(tags) if tags else ""
                    
                    # Is electric
                    is_electric = doc.get("is_electric", False)
                    
                    # Description
                    description = doc.get("description", "") or doc.get("product_card_description", "")
                    positioning = doc.get("positioning_phrase", "")
                    full_description = f"{positioning}. {description}".strip()
                    
                    # Main image - construct from variants
                    main_image = ""
                    if variants:
                        for v in variants:
                            if isinstance(v, dict) and "images" in v and v["images"]:
                                main_image = v["images"][0] if v["images"] else ""
                                break
                    
                    product = {
                        "id_produto": doc.get("salsify_id", ""),
                        "sku": sku,
                        "modelo": model_name,
                        "categoria": meta["categoria"],
                        "subcategoria": meta["subcategoria"],
                        "plataforma": meta["plataforma"],
                        "codigo_modelo": model_code,
                        "ano_modelo": year,
                        "cor": "",
                        "tamanho": sizes_str,
                        "material_quadro": material,
                        "peso": "",
                        "suspensao": suspension,
                        "freios": brakes,
                        "rodas": wheels,
                        "preco_site": price,
                        "moeda": "BRL",
                        "url_produto": product_url,
                        "descricao": full_description,
                        "url_imagem": main_image,
                        "url_imagem_principal": main_image,
                        "badges": badge_str,
                        "tags": tag_str,
                        "is_electric": is_electric,
                        "data_coleta": datetime.now().isoformat(),
                        "source_category_slug": slug,
                        "tipo_dado": "OFICIAL"
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
    print("=== CANNONDALE API SCRAPER - Fetching all products ===")
    
    all_products = []
    
    async with aiohttp.ClientSession() as session:
        for i, slug in enumerate(DEEP_SLUGS):
            meta = SLUG_META[slug]
            print(f"[{i+1}/{len(DEEP_SLUGS)}] {slug} ({meta['plataforma']})")
            products = await fetch_products_for_slug(session, slug)
            print(f"  Found {len(products)} products")
            all_products.extend(products)
    
    # Deduplicate by salsify_id
    seen = set()
    unique_products = []
    for p in all_products:
        if p["id_produto"] not in seen:
            seen.add(p["id_produto"])
            unique_products.append(p)
    
    print(f"\nTotal products fetched: {len(all_products)}")
    print(f"Unique products: {len(unique_products)}")
    
    # Save raw CSV
    out_file = RAW_DIR / "produtos_reais_api.csv"
    fieldnames = [
        "id_produto", "sku", "modelo", "categoria", "subcategoria", "plataforma",
        "codigo_modelo", "ano_modelo", "cor", "tamanho", "material_quadro", "peso",
        "suspensao", "freios", "rodas", "preco_site", "moeda", "url_produto",
        "descricao", "url_imagem", "url_imagem_principal", "badges", "tags",
        "is_electric", "data_coleta", "source_category_slug", "tipo_dado"
    ]
    
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in unique_products:
            writer.writerow(p)
    
    print(f"Saved {len(unique_products)} products to {out_file}")
    
    # Also save as JSON
    json_file = RAW_DIR / "produtos_reais_api.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(unique_products, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON to {json_file}")
    
    # Print summary
    print("\n=== SUMMARY BY CATEGORY ===")
    cat_counts = {}
    for p in unique_products:
        cat = p["categoria"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat}: {count}")
    
    print("\n=== SUMMARY BY PLATFORM ===")
    plat_counts = {}
    for p in unique_products:
        plat = p["plataforma"]
        plat_counts[plat] = plat_counts.get(plat, 0) + 1
    for plat, count in sorted(plat_counts.items()):
        print(f"  {plat}: {count}")
    
    print("\n=== PRODUCTS ===")
    for p in unique_products:
        print(f"  {p['modelo']} | {p['categoria']} | {p['subcategoria']} | {p['plataforma']} | R$ {p['preco_site']:,.2f} | {p['url_imagem'][:80] if p['url_imagem'] else 'NO IMAGE'}")

if __name__ == "__main__":
    asyncio.run(main())