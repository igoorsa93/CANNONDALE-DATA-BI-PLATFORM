"""Debug page structure to understand product link patterns"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    test_urls = [
        "https://www.cannondale.com/pt-br/bikes/road/race/caad14",
        "https://www.cannondale.com/pt-br/bikes/road/endurance/synapse",
        "https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/habit",
        "https://www.cannondale.com/pt-br/bikes/active/fitness/quick",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        for url in test_urls:
            print(f"\n=== {url} ===")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(8000)
                
                # Get all links
                links = await page.query_selector_all('a')
                print(f"Total links: {len(links)}")
                
                bike_links = []
                for link in links:
                    href = await link.get_attribute("href")
                    if href and "/bikes/" in href:
                        bike_links.append(href)
                
                print(f"Bike links: {len(bike_links)}")
                for l in bike_links[:30]:
                    print(f"  {l}")
                
                # Also check for product cards/grid
                product_cards = await page.query_selector_all('[class*="product"], [class*="Product"], [data-testid*="product"]')
                print(f"Product cards: {len(product_cards)}")
                
                # Check page content for JSON data
                content = await page.content()
                if "product" in content.lower() or "Product" in content:
                    # Look for JSON-LD or data attributes
                    import re
                    json_ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
                    if json_ld:
                        print(f"JSON-LD found: {len(json_ld)}")
                        for j in json_ld[:2]:
                            print(f"  {j[:500]}")
                            
            except Exception as e:
                print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())