"""Quick URL finder — tests candidate URLs and prints which return actual content."""
import asyncio
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

CANDIDATES = [
    # Argenprop
    ("Argenprop-1", "https://www.argenprop.com/cocheras/belgrano/alquiler"),
    ("Argenprop-2", "https://www.argenprop.com/busqueda?tipo-operacion=alquiler&tipo-propiedad=cochera&zona=belgrano"),
    ("Argenprop-3", "https://www.argenprop.com/cochera-alquiler-belgrano"),
    # Properati
    ("Properati-1", "https://www.properati.com.ar/s/belgrano_BSAS/cochera/alquiler/"),
    ("Properati-2", "https://www.properati.com.ar/cocheras/belgrano/alquiler/"),
    ("Properati-3", "https://www.properati.com.ar/s/belgrano/cochera/alquiler/"),
    # CabaProp
    ("CabaProp-1", "https://www.cabaprop.com.ar/buscar?tipo=alquiler&subtipo=cochera&barrio=belgrano"),
    ("CabaProp-2", "https://www.cabaprop.com.ar/cochera/alquiler/belgrano"),
    # Clasificados LN
    ("LaNacion-1", "https://clasificados.lanacion.com.ar/inmuebles/alquiler/cochera/belgrano"),
    # Zonaprop title test
    ("Zonaprop-1", "https://www.zonaprop.com.ar/cocheras-alquiler-belgrano.html"),
]


async def check(name, url, browser):
    ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
    page = await ctx.new_page()
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        title = await page.title()
        content = await page.content()
        size = len(content)
        status = resp.status if resp else "?"
        print(f"  [{status}] {name}: '{title[:60]}' ({size:,} bytes)")

        # For Zonaprop, find title selector
        if "zonaprop" in name.lower():
            for sel in ["[data-qa='POSTING_CARD_TITLE']", "h2.postingCardTitle", ".postingCard h2", "h2", "[class*='title']"]:
                els = await page.query_selector_all(sel)
                if els:
                    txt = await els[0].inner_text()
                    print(f"    Selector '{sel}' -> {len(els)} elements, first: '{txt[:50]}'")
                    break
    except Exception as e:
        print(f"  [ERR] {name}: {e}")
    finally:
        await ctx.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, url in CANDIDATES:
            await check(name, url, browser)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
