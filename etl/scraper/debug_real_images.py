"""Extract real image URLs from product page"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    # Test with a known product URL
    test_url = "https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo/supersix-evo-4"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Get all images
        images = await page.query_selector_all("img")
        print(f"Total images: {len(images)}")
        
        for img in images:
            src = await img.get_attribute("src")
            if src and ("cloudfront" in src or "media" in src):
                print(f"  {src}")
        
        # Also check for picture/source elements
        pictures = await page.query_selector_all("picture source")
        print(f"\nPicture sources: {len(pictures)}")
        for pic in pictures:
            srcset = await pic.get_attribute("srcset")
            if srcset:
                print(f"  {srcset[:200]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())