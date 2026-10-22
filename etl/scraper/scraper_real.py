"""
Pipeline Cannondale: Scraper real (Playwright) → Dados oficiais → Simulados → DB + Excel
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

async def extrair_produtos_categoria(page, url_categoria):
    """Extrai produtos de uma página de categoria."""
    await page.goto(url_categoria, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    
    # Buscar links de produtos
    links = await page.query_selector_all('a[href*="/bikes/"]')
    produtos = []
    
    for link in await page.query_selector_all('a[href*="/bikes/"]'):
        try:
            href = await link.get_attribute("href")
            if not href or not href.startswith("/pt-br/bikes/"):
                continue
            if href.count("/") < 4:  # pular páginas de categoria
                continue
            url_produto = f"https://www.cannondale.com{href}" if href.startswith("/") else href
            
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
            
            # Cor/Tamanho/Preço variam - pegar primeiro disponível
            cor = ""
            tamanho = ""
            
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
            
            # Determinar categoria pela URL
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

async def extrair_produtos_categoria(page, url_categoria):
    """Extrai produtos de uma página de categoria."""
    await page.goto(url_categoria, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)
    
    # Buscar links de produtos
    links = await page.query_selector_all('a[href*="/bikes/"]')
    
    for link in await page.query_selector_all('a[href*="/bikes/"]'):
        try:
            href = await link.get_attribute("href")
            if not href or not href.startswith("/pt-br/bikes/"):
                continue
            if href.count("/") < 4:  # pular páginas de categoria
                continue
            url_produto = f"https://www.cannondale.com{href}" if href.startswith("/") else href
            
            # Extrair dados do produto
            produto = await extrair_dados_produto(page, url_produto)
            if produto and produto.get("modelo"):
                yield produto
                
        except Exception as e:
            print(f"Erro ao extrair link: {e}")

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
            async for produto in extrair_produtos_categoria(page, url_categoria):
                print(f"  {produto['modelo'][:40]} | {produto['categoria']} | R$ {produto['preco_site']:,.2f}")
                produto["id_produto"] = str(uuid.uuid4())
                yield produto
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())