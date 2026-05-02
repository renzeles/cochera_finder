"""Find correct CSS selectors for each working portal."""
import asyncio
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

SITES = {
    "zonaprop": "https://www.zonaprop.com.ar/cocheras-alquiler-belgrano.html",
    "argenprop": "https://www.argenprop.com/cocheras/belgrano/alquiler",
    "properati": "https://www.properati.com.ar/s/belgrano/cochera/alquiler/",
}

CARD_CANDIDATES = {
    "zonaprop": [
        "[data-qa^='posting']",
        ".postingCard",
        "[data-posting-id]",
        "article",
    ],
    "argenprop": [
        ".card",
        ".listing-card",
        "article",
        "[class*='card']",
        ".card-grid",
    ],
    "properati": [
        ".listing-card",
        "article",
        "[class*='card']",
        ".property-item",
        "li[class*='item']",
    ],
}

TITLE_CANDIDATES = [
    "[data-qa='POSTING_CARD_TITLE']",
    ".postingCardTitle",
    "h2",
    "h3",
    "h2 a",
    "h3 a",
    "[class*='title'] a",
    "a[class*='title']",
    ".card-title",
    ".listing-title",
    "[class*='Title']",
]


async def analyze(name, url, browser):
    print(f"\n=== {name.upper()} ===")
    ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
    page = await ctx.new_page()
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Find card container
        print("Card containers:")
        best_card_sel = None
        for sel in CARD_CANDIDATES[name]:
            els = await page.query_selector_all(sel)
            print(f"  '{sel}' -> {len(els)} elements")
            if len(els) >= 3 and best_card_sel is None:
                best_card_sel = sel

        if best_card_sel:
            print(f"\nBest card selector: {best_card_sel}")
            card = (await page.query_selector_all(best_card_sel))[0]

            print("\nTitle candidates inside first card:")
            for sel in TITLE_CANDIDATES:
                el = await card.query_selector(sel)
                if el:
                    txt = await el.inner_text()
                    print(f"  '{sel}' -> '{txt[:60]}'")

            print("\nPrice candidates:")
            for sel in ["[data-qa*='PRICE']", "[class*='price']", "[class*='Price']", "span[class*='amount']"]:
                el = await card.query_selector(sel)
                if el:
                    txt = await el.inner_text()
                    print(f"  '{sel}' -> '{txt[:40]}'")

            print("\nLocation candidates:")
            for sel in ["[data-qa*='LOCATION']", "[class*='location']", "[class*='Location']", "[class*='address']", "[class*='Address']", "[class*='barrio']"]:
                el = await card.query_selector(sel)
                if el:
                    txt = await el.inner_text()
                    print(f"  '{sel}' -> '{txt[:60]}'")

            print("\nLink:")
            link = await card.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                print(f"  a -> '{href[:80]}'")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await ctx.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, url in SITES.items():
            await analyze(name, url, browser)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
