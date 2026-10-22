"""
Pipeline Cannondale: Scraper via Sitemap → Dados oficiais → Simulados → DB + Excel
"""
import asyncio
from playwright.async_api import async_playwright
import csv
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
import uuid
import re
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
IMAGES_DIR = Path("C:/Users/igoor/OneDrive/Desktop/CANNONDALE DATA & BI PLATFORM/Imagens")
DATABASE_DIR = Path(__file__).resolve().parents[1] / "database"

for d in [DATA_DIR / "raw", DATA_DIR / "processed", Path("C:/Users/igoor/OneDrive/Desktop/CANNONDALE DATA & BI PLATFORM/Imagens")]:
    d.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SITEMAP_BASE = 'https://a304077.sitemaphosting6.com/4356448/'

async def extrair_dados_produto(page, url_produto):
    """Extrai dados detalhados de uma página de produto."""
    try:
        await page.goto(url_produto, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(3000)
        
        # Nome real do produto
        h1 = await page.query_selector("h1")
        nome_real = await h1.inner_text() if h1 else ""
        if not nome_real or len(nome_real) < 3:
            nome_real = url_produto.split("/")[-2].replace("-", " ").title()
        
        # Preço
        preco = 0
        try:
            preco_el = await page.query_selector('[class*="price"], [data-testid*="price"], .price, [class*="Price"]')
            if preco_el:
                preco_txt = await preco_el.inner_text()
                import re
                nums = re.findall(r'[\d.,]+', preco_txt.replace(".", "").replace(",", "."))
                if nums:
                    preco = float(nums[0].replace(",", "."))
        except:
            pass
        
        # Imagem principal
        img_url = ""
        imgs = await page.query_selector_all("img")
        for img in imgs:
            src = await img.get_attribute("src")
            if src and "cloudfront" in src and "bikes" in src:
                if "mh=" in src and "mw=" in src:
                    img_url = src
                    break
        
        # Determinar categoria pela URL
        categoria = ""
        subcategoria = ""
        if "/road/" in url_produto:
            categoria = "Road"
            if "/gravel/" in url_produto:
                subcategoria = "Gravel"
            elif "/race/" in url_produto:
                subcategoria = "Race"
            elif "/endurance/" in url_produto:
                subcategoria = "Endurance"
        elif "/gravel/" in url_produto:
            categoria = "Gravel"
        elif "/mountain/" in url_produto:
            categoria = "Mountain"
            if "/cross-country/" in url_produto or "/cross-country" in url_produto:
                subcategoria = "Cross Country"
            elif "/trail" in url_produto or "/trail-" in url_produto:
                subcategoria = "Trail"
            elif "/enduro" in url_produto:
                subcategoria = "Enduro"
        elif "/electric/" in url_produto or "/e-" in url_produto:
            categoria = "Electric"
            if "/e-mountain/" in url_produto or "/e-mtb" in url_produto:
                subcategoria = "E-MTB"
            elif "/e-road/" in url_produto:
                subcategoria = "E-Road"
            elif "/e-urban/" in url_produto or "/e-cargo/" in url_produto:
                subcategoria = "E-Urban"
        elif "/active/" in url_produto:
            categoria = "Active"
            if "/urban/" in url_produto:
                subcategoria = "Urban"
            elif "/fitness/" in url_produto:
                subcategoria = "Fitness"
        elif "/kids/" in url_produto:
            categoria = "Kids"
        
        produto = {
            "id_produto": str(uuid.uuid4())[:8],
            "sku": url_produto.split("/")[-2],
            "modelo": "",
            "categoria": "",
            "subcategoria": "",
            "plataforma": "",
            "codigo_modelo": url_produto.split("/")[-2],
            "ano_modelo": 2026,
            "cor": "",
            "tamanho": "",
            "material_quadro": "",
            "peso": "",
            "preco_site": 0,
            "url_produto": "",
            "descricao": "",
            "url_imagem": "",
            "url_imagem_principal": "",
            "data_coleta": datetime.now().isoformat()
        }
        
        return produto
        
    except Exception as e:
        print(f"Erro ao processar {url_produto}: {e}")
        return None

async def main():
    print("=== CANNONDALE REAL DATA PIPELINE ===")
    
    # 1. Buscar URLs do sitemap
    print("Buscando URLs do sitemap...")
    import requests
    import re
    all_urls = []
    for sm in ['sitemap1.xml', 'sitemap2.xml']:
        try:
            r = requests.get(f"https://a304077.sitemaphosting6.com/4356448/{sm}", headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            urls = re.findall(r'<loc>(https?://www\.cannondale\.com/pt-br/bikes/[^<]+)</loc>', r.text)
            all_urls.extend(urls)
        except Exception as e:
            print(f"Erro sitemap: {e}")
    
    all_urls = sorted(set(all_urls))
    print(f'URLs totais: {len(all_urls)}')
    
    # Filtrar apenas URLs de produto (com ano)
    produtos_urls = [u for u in all_urls if any(x in u for x in ['2023', '2024', '2025', '2026', '2027'])]
    print(f'URLs de produtos: {len(produtos_urls)}')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        todos_produtos = []
        
        for i, url_produto in enumerate(produtos_urls[:50]):  # limitar para teste
            print(f"\n[{i+1}/{len(produtos_urls)}] {url_produto}")
            try:
                await page.goto(url_produto, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)
                
                # Nome real do produto
                h1 = await page.query_selector("h1")
                nome_real = await h1.inner_text() if h1 else ""
                if not nome_real or len(nome_real) < 3:
                    nome_real = url_produto.split("/")[-2].replace("-", " ").title()
                
                # Preço
                preco = 0
                try:
                    preco_el = await page.query_selector('[class*="price"], [data-testid*="price"], .price, [class*="Price"]')
                    if preco_el:
                        preco_txt = await preco_el.inner_text()
                        import re
                        nums = re.findall(r'[\d.,]+', preco_txt.replace(".", "").replace(",", "."))
                        if nums:
                            preco = float(nums[0].replace(",", "."))
                except:
                    pass
                
                # Imagem principal
                img_url = ""
                imgs = await page.query_selector_all("img")
                for img in imgs:
                    src = await img.get_attribute("src")
                    if src and "cloudfront" in src and "bikes" in src:
                        if "mh=" in src and "mw=" in src:
                            img_url = src
                            break
                
                # Determinar categoria pela URL
                categoria = ""
                subcategoria = ""
                if "/road/" in url_produto:
                    categoria = "Road"
                    if "/gravel/" in url_produto:
                        subcategoria = "Gravel"
                    elif "/race/" in url_produto:
                        subcategoria = "Race"
                    elif "/endurance/" in url_produto:
                        subcategoria = "Endurance"
                elif "/gravel/" in url_produto:
                    categoria = "Gravel"
                elif "/mountain/" in url_produto:
                    categoria = "Mountain"
                    if "/cross-country/" in url_produto or "/cross-country" in url_produto:
                        subcategoria = "Cross Country"
                    elif "/trail" in url_produto or "/trail-" in url_produto:
                        subcategoria = "Trail"
                    elif "/enduro" in url_produto:
                        subcategoria = "Enduro"
                elif "/electric/" in url_produto or "/e-" in url_produto:
                    categoria = "Electric"
                    if "/e-mountain/" in url_produto or "/e-mtb" in url_produto:
                        subcategoria = "E-MTB"
                    elif "/e-road/" in url_produto:
                        subcategoria = "E-Road"
                    elif "/e-urban/" in url_produto or "/e-cargo/" in url_produto:
                        subcategoria = "E-Urban"
                elif "/active/" in url_produto:
                    categoria = "Active"
                    if "/urban/" in url_produto:
                        subcategoria = "Urban"
                    elif "/fitness/" in url_produto:
                        subcategoria = "Fitness"
                elif "/kids/" in url_produto:
                    categoria = "Kids"
                
                produto = {
                    "id_produto": str(uuid.uuid4())[:8],
                    "sku": url_produto.split("/")[-2],
                    "modelo": "",
                    "categoria": "",
                    "subcategoria": "",
                    "plataforma": "",
                    "codigo_modelo": url_produto.split("/")[-2],
                    "ano_modelo": 2026,
                    "cor": "",
                    "tamanho": "",
                    "material_quadro": "",
                    "peso": "",
                    "preco_site": 0,
                    "url_produto": "",
                    "descricao": "",
                    "url_imagem": "",
                    "url_imagem_principal": "",
                    "data_coleta": datetime.now().isoformat()
                }
                
                produto["modelo"] = nome_real
                produto["categoria"] = categoria
                produto["subcategoria"] = subcategoria
                produto["preco_site"] = preco
                produto["url_produto"] = url_produto
                produto["url_imagem"] = img_url
                produto["url_imagem_principal"] = img_url
                produto["data_coleta"] = datetime.now().isoformat()
                
                print(f'  {nome_real[:30]:<30} | {categoria:<12} | R$ {preco:,.2f} | {img_url[:60]}')
                
            except Exception as e:
                print(f"Erro {url_produto}: {e}")
        
        # Salvar CSV
        out_file = Path("data/raw/produtos_reais.csv")
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["id_produto", "sku", "modelo", "categoria", "subcategoria", "plataforma", 
                         "codigo_modelo", "ano_modelo", "cor", "tamanho", "material_quadro", 
                             "peso", "preco_site", "url_produto", "descricao", "url_imagem", 
                             "url_imagem_principal", "data_coleta"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in todos_produtos:
                writer.writerow(p)
        
        print(f'\n✅ Salvos {len(todos_produtos)} produtos em data/raw/produtos_reais.csv')

if __name__ == "__main__":
    asyncio.run(main())