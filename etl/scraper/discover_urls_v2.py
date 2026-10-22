"""Discover all product URLs from Cannondale site - optimized"""
import asyncio
from playwright.async_api import async_playwright
import re

# Known family/platform URLs from sitemap and manual exploration
FAMILY_URLS = [
    # Road - Race
    "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo",
    "https://www.cannondale.com/pt-br/bikes/road/race/caad14",
    "https://www.cannondale.com/pt-br/bikes/road/race/caad13",
    "https://www.cannondale.com/pt-br/bikes/road/race/superslice",
    "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo-se",
    # Road - Gravel
    "https://www.cannondale.com/pt-br/bikes/road/gravel/superx",
    "https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-carbon",
    "https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-alloy",
    # Road - Endurance
    "https://www.cannondale.com/pt-br/bikes/road/endurance/synapse",
    # Road - Cyclocross
    "https://www.cannondale.com/pt-br/bikes/road/cyclocross/supersix-evo-cx",
    "https://www.cannondale.com/pt-br/bikes/road/cyclocross/caadx",
    # Mountain - Cross Country
    "https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel",
    "https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel-ht",
    "https://www.cannondale.com/pt-br/bikes/mountain/cross-country/f-si",
    "https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel-se",
    # Mountain - Trail
    "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/trail",
    "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/habit",
    "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/habit-ht",
    "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/dave",
    # Mountain - Enduro
    "https://www.cannondale.com/pt-br/bikes/mountain/enduro/jekyll",
    "https://www.cannondale.com/pt-br/bikes/mountain/enduro/bad-habit",
    # Electric - E-MTB
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain/moterra-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain/moterra-neo-lt",
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain/moterra-sl",
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain/trail-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-mountain/habit-neo",
    # Electric - E-Road
    "https://www.cannondale.com/pt-br/bikes/electric/e-road/topstone-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-road/synapse-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-road/supersix-evo-neo",
    # Electric - E-Urban
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban/compact-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban/flyingv",
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban/adventure-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban/mavaro",
    "https://www.cannondale.com/pt-br/bikes/electric/e-urban/canvas-neo",
    # Electric - E-Touring
    "https://www.cannondale.com/pt-br/bikes/electric/e-touring/tesoro",
    "https://www.cannondale.com/pt-br/bikes/electric/e-touring/tesoro-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-touring/tesoro-neo-x",
    # Electric - E-Cargo
    "https://www.cannondale.com/pt-br/bikes/electric/e-cargo/cargowagen-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-cargo/wonderwagen-neo",
    # Electric - E-Fitness
    "https://www.cannondale.com/pt-br/bikes/electric/e-fitness/quick-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-fitness/treadwell-neo",
    "https://www.cannondale.com/pt-br/bikes/electric/e-fitness/quick-neo-sl",
    # Active - Fitness
    "https://www.cannondale.com/pt-br/bikes/active/fitness/quick",
    "https://www.cannondale.com/pt-br/bikes/active/fitness/quick-cx",
    "https://www.cannondale.com/pt-br/bikes/active/fitness/treadwell",
    "https://www.cannondale.com/pt-br/bikes/active/fitness/adventure",
    # Active - Urban
    "https://www.cannondale.com/pt-br/bikes/active/urban/bad-boy",
    # Kids
    "https://www.cannondale.com/pt-br/bikes/kids/5-to-8",
    "https://www.cannondale.com/pt-br/bikes/kids/7-to-12",
]

async def discover_product_urls(page, url):
    """Discover product URLs from a family page"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        
        product_urls = set()
        
        # Get all links on page
        links = await page.query_selector_all('a[href*="/bikes/"]')
        
        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.cannondale.com{href}"
            
            # Product URLs typically have year at the end
            if re.search(r'/202[3-7](?:/|$)', href):
                product_urls.add(href)
            # Also check for product variant pages (deep URLs without year)
            elif href.count('/') >= 7 and '/bikes/' in href:
                product_urls.add(href)
        
        return product_urls
    except Exception as e:
        print(f"  Error: {e}")
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
        
        for i, fam_url in enumerate(FAMILY_URLS):
            print(f"[{i+1}/{len(FAMILY_URLS)}] {fam_url}")
            urls = await discover_product_urls(page, fam_url)
            all_product_urls.update(urls)
            print(f"  Found {len(urls)} product URLs")
        
        await browser.close()
    
    # Save discovered URLs
    with open("data/raw/discovered_product_urls.txt", "w") as f:
        for url in sorted(all_product_urls):
            f.write(url + "\n")
    
    print(f"\nTotal unique product URLs discovered: {len(all_product_urls)}")
    for url in sorted(all_product_urls):
        print(url)

if __name__ == "__main__":
    asyncio.run(main())