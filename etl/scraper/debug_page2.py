"""Debug product cards to find actual product links"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    test_url = "https://www.cannondale.com/pt-br/bikes/road/race/caad14"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        
        # Check product cards
        product_cards = await page.query_selector_all('[class*="product"], [class*="Product"], [data-testid*="product"]')
        print(f"Product cards: {len(product_cards)}")
        
        for i, card in enumerate(product_cards):
            print(f"\n--- Card {i} ---")
            # Get all links inside card
            links = await card.query_selector_all('a')
            for link in links:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                print(f"  Link: {href} | Text: {text[:50]}")
            
            # Get card HTML
            html = await card.inner_html()
            print(f"  HTML (first 500): {html[:500]}")
        
        # Also check for buttons or clickable elements
        buttons = await page.query_selector_all('button, [role="button"], [class*="cta"], [class*="CTA"]')
        print(f"\nButtons: {len(buttons)}")
        for btn in buttons[:10]:
            text = await btn.inner_text()
            print(f"  Button: {text[:50]}")
        
        # Check for data attributes on product elements
        elements = await page.query_selector_all('[data-product], [data-sku], [data-model]')
        print(f"\nElements with data-product/sku/model: {len(elements)}")
        for el in elements[:10]:
            print(f"  {await el.get_attribute('data-product') or await el.get_attribute('data-sku') or await el.get_attribute('data-model')}")
        
        # Look for JSON data in page
        content = await page.content()
        import re
        # Look for product data in scripts
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        for script in scripts:
            if 'product' in script.lower() and ('sku' in script.lower() or 'price' in script.lower() or 'model' in script.lower()):
                print(f"\nRelevant script found (first 1000): {script[:1000]}")
                break
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())