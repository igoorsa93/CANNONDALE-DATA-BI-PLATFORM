"""Search for all products to discover actual category slugs"""
import asyncio
import aiohttp
import json

TYPESENSE_HOST = "th2gn1fbwadp739ep.a1.typesense.net"
TYPESENSE_COLLECTION = "prod-cd-products_v19"
TYPESENSE_API_KEY = "QaHJa8YV4lky2rkXT6BiA5JPCKeegOOy"

async def search_all_products():
    url = f"https://{TYPESENSE_HOST}/collections/{TYPESENSE_COLLECTION}/documents/search"
    
    params = {
        "q": "*",
        "query_by": "model_name,model_code,consumer_name_3,salsify_id,skus,category,sub_category,segment,platform,brand",
        "filter_by": "country:=BR && has_price:=true && product_type:=Bike",
        "per_page": "250",
        "page": "1",
        "include_fields": "salsify_id,relative_url,name,consumer_name_1,consumer_name_2,consumer_name_3,brand,platform,active_model_year,genders,category,sub_category,product_type,category_slugs"
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
                print(f"Found {data.get('found', 0)} total products")
                print(f"Returned {len(hits)} products (page 1)")
                
                # Collect all unique category_slugs
                all_slugs = set()
                for hit in hits:
                    doc = hit.get("document", {})
                    slugs = doc.get("category_slugs", [])
                    if isinstance(slugs, list):
                        for s in slugs:
                            all_slugs.add(s)
                    elif isinstance(slugs, str):
                        all_slugs.add(slugs)
                
                print(f"\nUnique category_slugs found ({len(all_slugs)}):")
                for s in sorted(all_slugs):
                    print(f"  {s}")
                
                # Also show sample products
                print("\n=== Sample Products ===")
                for hit in hits[:10]:
                    doc = hit.get("document", {})
                    print(f"  {doc.get('consumer_name_3', doc.get('name', 'N/A'))} | {doc.get('platform', 'N/A')} | {doc.get('category_slugs', [])}")
                
                # Save slugs to file
                with open("data/raw/category_slugs.txt", "w") as f:
                    for s in sorted(all_slugs):
                        f.write(s + "\n")
                print("\n✅ Saved category slugs to data/raw/category_slugs.txt")
            else:
                print(f"Error: {resp.status}")
                text = await resp.text()
                print(text[:1000])

if __name__ == "__main__":
    asyncio.run(search_all_products())