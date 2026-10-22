"""Debug variants structure for a product"""
import asyncio
import aiohttp
import json

TYPESENSE_HOST = "th2gn1fbwadp739ep.a1.typesense.net"
TYPESENSE_COLLECTION = "prod-cd-products_v19"
TYPESENSE_API_KEY = "QaHJa8YV4lky2rkXT6BiA5JPCKeegOOy"

async def debug_variants():
    url = f"https://{TYPESENSE_HOST}/collections/{TYPESENSE_COLLECTION}/documents/search"
    
    params = {
        "q": "*",
        "query_by": "model_name,model_code,consumer_name_3,salsify_id,skus,category,sub_category,segment,platform,brand",
        "filter_by": "country:=BR && has_price:=true && (product_type:=Bike && category_slugs:=[road--race--supersix-evo])",
        "per_page": "5",
        "page": "1",
        "include_fields": "salsify_id,relative_url,name,consumer_name_3,variants"
    }
    
    headers = {
        "X-TYPESENSE-API-KEY": TYPESENSE_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                hits = data.get("hits", [])
                
                for hit in hits:
                    doc = hit.get("document", {})
                    print(f"\n=== {doc.get('consumer_name_3', 'N/A')} ===")
                    print(f"salsify_id: {doc.get('salsify_id')}")
                    print(f"relative_url: {doc.get('relative_url')}")
                    
                    variants = doc.get("variants", [])
                    print(f"variants count: {len(variants)}")
                    for i, v in enumerate(variants):
                        print(f"\n  Variant {i}:")
                        print(json.dumps(v, indent=4, ensure_ascii=False)[:2000])
            else:
                print(f"Error: {resp.status}")

if __name__ == "__main__":
    asyncio.run(debug_variants())