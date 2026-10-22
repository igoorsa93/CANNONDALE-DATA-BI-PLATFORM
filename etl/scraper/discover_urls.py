"""Discover all product URLs from Cannondale site"""
import asyncio
from playwright.async_api import async_playwright
import re

CATEGORY_URLS = [
    "https://www.cannondale.com/pt-br/bikes/road",
    "https://www.cannondale.com/pt-br/bikes/road/gravel",
    "https://www.cannondale.com/pt-br/bikes/road/endurance",
    "https://www.cannondale.com/pt-br/bikes/road/race",
    "https://www.cannondale.com/pt-br/bikes/road/cyclocross",
    "https://www.cannondale.com/pt-br/bikes/mountain",
    "https://www.cannondale.com/pt-br/bikes/mountain/cross-country",
    "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes",
    "https://www.cannondale.com/pt-br/bikes/mountain/enduro",
    "https://www.cannondale.com/pt-br/bikes/electric",
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain",
    "https://www.cannondale.com/pt-br/bikes/electric/e-road",
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban",
    "https://www.cannondale.com/pt-br/bikes/electric/e-touring",
    "https://www.cannondale.com/pt-br/bikes/electric/e-cargo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-fitness",
    "https://www.cannondale.com/pt-br/bikes/active",
    "https://www.cannondale.com/pt-br/bikes/active/fitness",
    "https://www.cannondale.com/pt-br/bikes/active/urban",
    "https://www.cannondale.com/pt-br/bikes/kids",
    "https://www.cannondale.com/pt-br/bikes/kids/1-to-4",
    "https://www.cannondale.com/pt-br/bikes/kids/5-to-8",
    "https://www.cannondale.com/pt-br/bikes/kids/7-to-12",
]

async def discover_product_urls(page, url):
    """Discover product URLs from a category/family page"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Get all links
        links = await page.query_selector_all('a[href*="/bikes/"]')
        product_urls = set()
        
        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.cannondale.com{href}"
            
            # Check if it's a product URL (contains year)
            if re.search(r'/202[3-7](?:/|$)', href):
                product_urls.add(href)
            # Also check for product-like URLs without year but deep enough
            elif href.count('/') >= 6 and '/bikes/' in href:
                product_urls.add(href)
        
        return product_urls
    except Exception as e:
        print(f"Error discovering {url}: {e}")
        return set()

async def main():
    all_product_urls = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # First, discover family/category pages from main category URLs
        family_urls = set()
        for cat_url in CATEGORY_URLS:
            print(f"Discovering families from: {cat_url}")
            try:
                await page.goto(cat_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                links = await page.query_selector_all('a[href*="/bikes/"]')
                for link in links:
                    href = await link.get_attribute("href")
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = f"https://www.cannondale.com{href}"
                    # Family pages are typically 4-5 levels deep
                    if href.count('/') >= 5 and '/bikes/' in href:
                        family_urls.add(href)
            except Exception as e:
                print(f"Error on {cat_url}: {e}")
        
        print(f"\nFound {len(family_urls)} family/category pages")
        
        # Now discover products from each family page
        for i, fam_url in enumerate(sorted(family_urls)):
            print(f"[{i+1}/{len(family_urls)}] Discovering products from: {fam_url}")
            urls = await discover_product_urls(page, fam_url)
            all_product_urls.update(urls)
            print(f"  Found {len(urls)} product URLs")
        
        await browser.close()
    
    # Save discovered URLs
    with open("data/raw/discovered_product_urls.txt", "w") as f:
        for url in sorted(all_product_urls):
            f.write(url + "\n")
    
    print(f"\nTotal unique product URLs discovered: {len(all_product_urls)}")

if __name__ == "__main__":
    asyncio.run(main())