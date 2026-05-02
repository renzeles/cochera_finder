"""
Saves the rendered HTML of each portal to debug/ so we can inspect the actual structure.
"""
import asyncio
import os
from playwright.async_api import async_playwright

SITES = {
    "zonaprop": "https://www.zonaprop.com.ar/cocheras-alquiler-belgrano.html",
    "argenprop": "https://www.argenprop.com/cochera/alquilar/belgrano",
    "mercadolibre": "https://inmuebles.mercadolibre.com.ar/cocheras/alquiler/belgrano/",
    "properati": "https://www.properati.com.ar/cochera/belgrano/alquiler/",
    "olx": "https://www.olx.com.ar/items/q-cochera-belgrano",
    "cabaprop": "https://www.cabaprop.com.ar/cocheras-alquiler-belgrano",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def main():
    os.makedirs("debug", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, url in SITES.items():
            print(f"Fetching {name}...")
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
            page = await ctx.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)
                html = await page.content()
                path = f"debug/{name}.html"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                size = len(html)
                print(f"  Saved {path} ({size:,} bytes)")
            except Exception as e:
                print(f"  ERROR: {e}")
            await ctx.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
