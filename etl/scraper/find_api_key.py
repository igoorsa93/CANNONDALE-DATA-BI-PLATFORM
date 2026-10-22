"""Find the Typesense API key used by the site"""
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
        
        # Capture the Typesense request with headers
        typesense_request = None
        
        async def handle_request(request):
            nonlocal typesense_request
            if "typesense" in request.url and "search" in request.url:
                typesense_request = {
                    "url": request.url,
                    "headers": request.headers
                }
                print(f"Typesense request found!")
                print(f"URL: {request.url}")
                print(f"Headers: {request.headers}")
        
        page.on("request", handle_request)
        
        await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)
        
        if not typesense_request:
            print("No Typesense request captured")
            # Check if there's a script that makes the request
            content = await page.content()
            import re
            # Look for API key in scripts
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
            for script in scripts:
                if 'typesense' in script.lower() or 'api.*key' in script.lower() or 'x-typesense' in script.lower():
                    print(f"Found relevant script: {script[:1000]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())