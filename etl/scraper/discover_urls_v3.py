"""Discover all individual product URLs from Cannondale site"""
import asyncio
from playwright.async_api import async_playwright
import re

# Known family/platform URLs
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

def is_product_url(url):
    """Check if URL is an individual product page (not family/category)"""
    # Product URLs have model identifiers like -1, -2, -3, or specific model names
    # They typically end with a model identifier or year
    # Family pages don't have trailing model numbers
    
    # Skip family/collection pages
    family_indicators = [
        '/supersix-evo$', '/caad14$', '/caad13$', '/superslice$', '/supersix-evo-se$',
        '/superx$', '/topstone-carbon$', '/topstone-alloy$', '/synapse$',
        '/supersix-evo-cx$', '/caadx$', '/scalpel$', '/scalpel-ht$', '/f-si$', '/scalpel-se$',
        '/trail$', '/habit$', '/habit-ht$', '/dave$', '/jekyll$', '/bad-habit$',
        '/moterra-neo$', '/moterra-neo-lt$', '/moterra-sl$', '/trail-neo$', '/habit-neo$',
        '/topstone-neo$', '/synapse-neo$', '/supersix-evo-neo$',
        '/compact-neo$', '/flyingv$', '/adventure-neo$', '/mavaro$', '/canvas-neo$',
        '/tesoro$', '/tesoro-neo$', '/tesoro-neo-x$',
        '/cargowagen-neo$', '/wonderwagen-neo$',
        '/quick-neo$', '/treadwell-neo$', '/quick-neo-sl$',
        '/quick$', '/quick-cx$', '/treadwell$', '/adventure$',
        '/bad-boy$',
        '/5-to-8$', '/7-to-12$',
    ]
    
    for indicator in family_indicators:
        if re.search(indicator, url):
            return False
    
    # Product URLs typically have model suffixes
    # e.g., /supersix-evo-1, /scalpel-1, /topstone-carbon-3, etc.
    if re.search(r'/(supersix-evo|caad|superslice|superx|topstone|synapse|scalpel|habit|jekyll|moterra|trail|tesoro|quick|treadwell|adventure|bad-boy|f-si|dave|compact-neo|flyingv|mavaro|canvas|cargowagen|wonderwagen|synapse-neo|supersix-evo-neo|topstone-neo)-(?:[1-9]|[1-9][0-9]|lab71|hi-mod|sl|se|cx|neo|allroad|carbon|alloy)(?:-[a-z0-9]+)*(?:/202[3-7])?(?:/|$)', url, re.IGNORECASE):
        return True
    
    # Also check for URLs with year at the end (product pages)
    if re.search(r'/202[3-7](?:/|$)', url):
        # But exclude family pages that happen to have year
        if url.count('/') >= 7:
            return True
    
    return False

async def discover_product_urls(page, url):
    """Discover individual product URLs from a family page"""
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
            
            if is_product_url(href):
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
    
    # Also add known product URLs from sitemap
    known_products = [
        "https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel/scalpel-lab71/2024",
        "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-lab71/2023",
        "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-2/2023",
        "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-lab71-frameset/2023",
        "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-lab71/2024",
        "https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-carbon/topstone-carbon-2-lefty/2023",
        "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-1/2023",
    ]
    for url in known_products:
        all_product_urls.add(url)
    
    # Save discovered URLs
    with open("data/raw/discovered_product_urls.txt", "w") as f:
        for url in sorted(all_product_urls):
            f.write(url + "\n")
    
    print(f"\nTotal unique product URLs discovered: {len(all_product_urls)}")
    for url in sorted(all_product_urls):
        print(url)

if __name__ == "__main__":
    asyncio.run(main())