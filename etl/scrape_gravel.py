#!/usr/bin/env python3
"""
Scrape Gravel category from Cannondale official site
"""
import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
IMAGES_DIR = ROOT / "Imagens"

for d in [RAW_DIR, IMAGES_DIR / "Gravel"]:
    d.mkdir(parents=True, exist_ok=True)

GRAVEL_URLS = [
    "https://www.cannondale.com/pt-br/bikes/road/gravel",
    "https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-carbon",
    "https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-alloy",
    "https://www.cannondale.com/pt-br/bikes/road/gravel/superx",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

CLOUDFRONT_BASE = "https://d1mo5ln9tjltxq.cloudfront.net"

async def extract_product_data(page, url_produto):
    """Extract detailed product data from product page"""
    try:
        await page.goto(url_produto, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Get product name
        h1 = await page.query_selector("h1")
        nome_real = await h1.inner_text() if h1 else ""
        if not nome_real or len(nome_real) < 3:
            nome_real = url_produto.split("/")[-2].replace("-", " ").title()
        
        # Extract price
        preco = 0
        try:
            preco_el = await page.query_selector('[class*="price"], [data-testid*="price"], .price, [class*="Price"]')
            if preco_el:
                preco_txt = await preco_el.inner_text()
                nums = re.findall(r'[\d.,]+', preco_txt.replace(".", "").replace(",", "."))
                if nums:
                    preco = float(nums[0].replace(",", "."))
        except:
            pass
        
        # Extract specifications
        specs = {}
        try:
            spec_elements = await page.query_selector_all('[class*="spec"], [class*="Spec"], [data-testid*="spec"]')
            for el in spec_elements:
                text = await el.inner_text()
                if ":" in text:
                    key, val = text.split(":", 1)
                    specs[key.strip()] = val.strip()
        except:
            pass
        
        # Get main image
        img_url = ""
        try:
            imgs = await page.query_selector_all("img")
            for img in imgs:
                src = await img.get_attribute("src")
                if src and "cloudfront" in src and "bikes" in src:
                    if "mh=" in src and "mw=" in src:
                        img_url = src
                        break
        except:
            pass
        
        # Determine category/subcategory from URL
        categoria = "Road"
        subcategoria = "Gravel"
        plataforma = ""
        
        if "/superx" in url_produto:
            plataforma = "SuperX"
        elif "/topstone-carbon" in url_produto:
            plataforma = "Topstone Carbon"
        elif "/topstone-alloy" in url_produto:
            plataforma = "Topstone Alloy"
        
        # Generate product ID
        id_produto = url_produto.split("/")[-2]
        if id_produto.endswith("/"):
            id_produto = id_produto[:-1]
        
        produto = {
            "id_produto": id_produto,
            "modelo": nome_real,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "plataforma": plataforma,
            "preco_site": preco,
            "moeda": "BRL",
            "url_produto": url_produto,
            "url_imagem_principal": img_url,
            "especificacoes": json.dumps(specs, ensure_ascii=False),
            "data_coleta": datetime.now().isoformat(),
            "fonte": "Cannondale Oficial",
            "tipo_dado": "OFICIAL"
        }
        
        return produto
        
    except Exception as e:
        print(f"Erro ao processar {url_produto}: {e}")
        return None

async def discover_product_urls(page, url_categoria):
    """Discover all product URLs from a category page"""
    try:
        await page.goto(url_categoria, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        
        product_urls = set()
        
        # Get all links
        links = await page.query_selector_all('a[href*="/bikes/"]')
        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.cannondale.com{href}"
            
            # Check if it's a product URL (contains year or deep path)
            if re.search(r'/202[3-7](?:/|$)', href):
                product_urls.add(href)
            elif href.count('/') >= 7 and '/bikes/' in href:
                product_urls.add(href)
        
        return product_urls
    except Exception as e:
        print(f"Erro ao descobrir {url_categoria}: {e}")
        return set()

async def main():
    print("=== CANNONDALE GRAVEL SCRAPER ===")
    
    all_products = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        for url in GRAVEL_URLS:
            print(f"Processando: {url}")
            urls = await discover_product_urls(page, url)
            print(f"  Encontradas {len(urls)} URLs de produtos")
            
            for url_produto in urls:
                produto = await extract_product_data(page, url_produto)
                if produto:
                    all_products.append(produto)
                    print(f"  [OK] {produto['modelo']} | R$ {produto['preco_site']:,.2f}")
        
        await browser.close()
    
    # Save results
    output_file = Path("data/raw/gravel_products.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    # Also save as CSV
    if all_products:
        import csv
        csv_file = Path("data/raw/gravel_products.csv")
        fieldnames = ["id_produto", "modelo", "categoria", "subcategoria", "plataforma", 
                     "preco_site", "moeda", "url_produto", "url_imagem_principal", 
                     "especificacoes", "data_coleta", "fonte", "tipo_dado"]
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in all_products:
                writer.writerow(p)
    
    print(f"\n✅ Total produtos Gravel: {len(all_products)}")
    print(f"Salvo em: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())