"""Debug to find API endpoints for product grid"""
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
        
        # Capture network requests
        requests_made = []
        page.on("request", lambda req: requests_made.append(req.url) if "api" in req.url or "product" in req.url or "plp" in req.url or "grid" in req.url else None)
        page.on("response", lambda resp: print(f"RESPONSE: {resp.url} - {resp.status}") if "api" in resp.url or "product" in resp.url or "plp" in resp.url or "grid" in resp.url else None)
        
        await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)
        
        print("\n=== All captured requests ===")
        for req in requests_made:
            print(req)
        
        # Try to find product grid container and see if it loads via AJAX
        content = await page.content()
        import re
        # Look for API endpoints in scripts
        scripts = re.findall(r'<script[^>]*src=["\']([^\'"]+)', content)
        for s in scripts:
            if 'api' in s or 'product' in s or 'plp' in s:
                print(f"Script src: {s}")
        
        # Check for product grid container
        grid = await page.query_selector('[class*="product-grid"], [class*="ProductGrid"], [id*="product-grid"], [data-testid*="product-grid"]')
        if grid:
            print(f"\nProduct grid found: {await grid.get_attribute('class')}")
            html = await grid.inner_html()
            print(f"Grid HTML (first 1000): {html[:1000]}")
        else:
            print("\nNo product grid container found")
            # Check for any container that might hold products
            containers = await page.query_selector_all('[class*="grid"], [class*="Grid"], [class*="list"], [class*="List"]')
            for c in containers[:10]:
                cls = await c.get_attribute('class')
                print(f"  Container: {cls}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())