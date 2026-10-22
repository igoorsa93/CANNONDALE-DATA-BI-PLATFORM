"""Debug the exact API request that works"""
import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    test_url = "https://www.cannondale.com/pt-br/bikes/road/race/caad14"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Capture the Typesense request AND response
        typesense_data = {}
        
        async def handle_request(request):
            if "typesense" in request.url and "search" in request.url:
                typesense_data["request_url"] = request.url
                typesense_data["request_headers"] = request.headers
        
        async def handle_response(response):
            if "typesense" in response.url and "search" in response.url:
                typesense_data["response_status"] = response.status
                try:
                    typesense_data["response_body"] = await response.json()
                except:
                    typesense_data["response_text"] = await response.text()
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        await page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)
        
        if typesense_data:
            print("=== REQUEST ===")
            print(typesense_data.get("request_url", "N/A"))
            print("\n=== HEADERS ===")
            print(json.dumps(typesense_data.get("request_headers", {}), indent=2))
            print("\n=== RESPONSE ===")
            print(f"Status: {typesense_data.get('response_status', 'N/A')}")
            if "response_body" in typesense_data:
                print(json.dumps(typesense_data["response_body"], indent=2)[:5000])
            elif "response_text" in typesense_data:
                print(typesense_data["response_text"][:5000])
        else:
            print("No Typesense data captured")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())