import asyncio
from .utils import parse_precio, normalize_address

SEARCH_URL = "https://www.olx.com.ar/items/q-cochera-belgrano"
MAX_PAGES = 3


async def scrape_olx(context):
    listings = []
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    for page_num in range(1, MAX_PAGES + 1):
        url = SEARCH_URL if page_num == 1 else f"{SEARCH_URL}?page={page_num}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception:
            break

        cards = await page.query_selector_all(
            "li[data-aut-id='itemBox'], .item-box, [class*='listing-item']"
        )
        if not cards:
            break

        for card in cards:
            try:
                titulo_el = await card.query_selector(
                    "[data-aut-id='itemTitle'], h2, h3, [class*='title']"
                )
                titulo = await titulo_el.inner_text() if titulo_el else ""

                precio_el = await card.query_selector(
                    "[data-aut-id='itemPrice'], [class*='price']"
                )
                precio_txt = await precio_el.inner_text() if precio_el else ""

                loc_el = await card.query_selector(
                    "[data-aut-id='item-location'], [class*='location'], [class*='address']"
                )
                direccion_txt = await loc_el.inner_text() if loc_el else "Belgrano, CABA"

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                url_listing = href if href.startswith("http") else f"https://www.olx.com.ar{href}"

                if not titulo:
                    continue

                listings.append({
                    "titulo": titulo.strip(),
                    "precio": precio_txt.strip(),
                    "precio_num": parse_precio(precio_txt),
                    "direccion": normalize_address(direccion_txt),
                    "url": url_listing,
                    "descripcion": "",
                })
            except Exception:
                continue

        if len(cards) < 20:
            break

    await page.close()
    return listings
