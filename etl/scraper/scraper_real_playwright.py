"""
Pipeline completo Cannondale: Scraper real (Playwright) → Dados oficiais → Simulados → DB + Excel
"""
import asyncio
from playwright.async_api import async_playwright
import json
import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
import uuid

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
IMAGES_DIR = ROOT / "Imagens"
DATABASE_DIR = ROOT / "database"

for d in [RAW_DIR, PROCESSED_DIR, IMAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

CATEGORIAS_URL = [
    "https://www.cannondale.com/pt-br/bikes/road",
    "https://www.cannondale.com/pt-br/bikes/road/gravel",
    "https://www.cannondale.com/pt-br/bikes/mountain",
    "https://www.cannondale.com/pt-br/bikes/electric",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

async def extrair_produtos_categoria(page, url_categoria, categoria):
    """Extrai produtos de uma página de categoria."""
    await page.goto(url_categoria, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    
    # Buscar cards de produtos
    cards = await page.query_selector_all('a[href*="/bikes/"]')
    produtos = []
    
    for card in cards[:50]:  # limite por categoria
        try:
            href = await card.get_attribute("href")
            if not href or not href.startswith("/pt-br/bikes/"):
                continue
            
            # Tentar pegar nome do modelo
            texto = await card.inner_text()
            if len(texto.strip()) < 3:
                continue
                
            # Construir URL completa
            url_produto = f"https://www.cannondale.com{href}" if href.startswith("/") else href
            
            # Extrair nome do modelo do texto ou URL
            nome_modelo = texto.strip() if texto.strip() else href.split("/")[-2]
            
            # Acessar página do produto para pegar detalhes
            await page.goto(url_produto, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            
            # Nome real do produto
            h1 = await page.query_selector("h1")
            nome_real = await h1.inner_text() if h1 else ""
            if not nome_real or len(nome_real) < 3:
                nome_real = url_produto.split("/")[-2].replace("-", " ").title()
            
            # Preço
            preco = 0
            try:
                preco_el = await page.query_selector('[class*="price"], [data-testid*="price"], .price')
                if preco_el:
                    preco_txt = await preco_el.inner_text()
                    # Extrair número
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
                    # Pega a maior resolução
                    if "mh=" in src and "mw=" in src:
                        img_url = src
                        break
            
            # Cor/Tamanho/Preço variam - pegar primeiro disponível
            cor = ""
            tamanho = ""
            try:
                # Tentar achar selects de cor/tamanho
                pass
            except:
                pass
            
            produto = {
                "id_produto": str(uuid.uuid4())[:8],
                "sku": url_produto.split("/")[-2],
                "modelo": nome_real.strip(),
                "categoria": "",  # será preenchido
                "subcategoria": "",
                "plataforma": "",
                "codigo_modelo": url_produto.split("/")[-2],
                "ano_modelo": 2026,
                "cor": "",
                "tamanho": "",
                "material_quadro": "",
                "peso": "",
                "preco_site": preco,
                "url_produto": url_produto,
                "descricao": "",
                "url_imagem": url_produto,
                "url_imagem_principal": url_produto,
                "data_coleta": datetime.now().isoformat()
            }
            
            # Determinar categoria pela URL
            if "/road/" in url_produto:
                produto["categoria"] = "Road"
                if "/gravel/" in url_produto:
                    produto["subcategoria"] = "Gravel"
                elif "/race/" in url_produto:
                    produto["subcategoria"] = "Race"
                elif "/endurance/" in url_produto:
                    produto["subcategoria"] = "Endurance"
            elif "/gravel/" in url_produto:
                produto["categoria"] = "Gravel"
                produto["subcategoria"] = "Gravel"
            elif "/mountain/" in url_produto:
                produto["categoria"] = "Mountain"
                if "/cross-country/" in url_produto or "/cross-country" in url_produto:
                    produto["subcategoria"] = "Cross Country"
                elif "/trail" in url_produto or "/trail-" in url_produto:
                    produto["subcategoria"] = "Trail"
                elif "/enduro" in url_produto:
                    produto["subcategoria"] = "Enduro"
            elif "/electric/" in url_produto or "/e-" in url_produto:
                produto["categoria"] = "Electric"
                if "/e-mountain/" in url_produto or "/e-mtb" in url_produto:
                    produto["subcategoria"] = "E-MTB"
                elif "/e-road/" in url_produto:
                    produto["subcategoria"] = "E-Road"
                elif "/e-urban/" in url_produto or "/e-cargo/" in url_produto:
                    produto["subcategoria"] = "E-Urban"
            elif "/active/" in url_produto:
                produto["categoria"] = "Active"
                produto["subcategoria"] = "Urban" if "/urban/" in url_produto else "Fitness"
            elif "/kids/" in url_produto:
                produto["categoria"] = "Kids"
            
            yield produto
            
        except Exception as e:
            print(f"Erro ao processar {url_produto}: {e}")

async def main():
    print("=== CANNONDALE REAL DATA PIPELINE ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        todos_produtos = []
        
        for url_cat in CATEGORIAS_URL:
            print(f"\n=== Processando {url_cat} ===")
            async for produto in extrair_produtos_categoria(page, url_cat, ""):
                print(f"  {produto['modelo'][:40]} | {produto['categoria']} | R$ {produto['preco_site']:,.2f}")
                produto["id_produto"] = str(uuid.uuid4())
                yield produto
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())