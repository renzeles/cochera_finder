import asyncio
from .utils import parse_precio, normalize_address

BASE_URL = "https://www.zonaprop.com.ar/cocheras-alquiler-belgrano"
MAX_PAGES = 5


async def scrape_zonaprop(context):
    listings = []
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    for page_num in range(1, MAX_PAGES + 1):
        url = BASE_URL + ".html" if page_num == 1 else f"{BASE_URL}-pagina-{page_num}.html"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception:
            break

        cards = await page.query_selector_all("[data-qa^='posting']")
        if not cards:
            break

        for card in cards:
            try:
                # Title is in h2 > a
                titulo_el = await card.query_selector("h2 a")
                titulo = await titulo_el.inner_text() if titulo_el else ""

                precio_el = await card.query_selector("[data-qa*='PRICE'], [class*='price']")
                precio_txt = await precio_el.inner_text() if precio_el else ""

                # Prefer specific street address over zone name
                addr_el = await card.query_selector("[class*='address']")
                addr_txt = await addr_el.inner_text() if addr_el else ""

                loc_el = await card.query_selector("[data-qa*='LOCATION']")
                loc_txt = await loc_el.inner_text() if loc_el else ""

                # Combine street + zone for geocoding accuracy
                if addr_txt and loc_txt:
                    direccion_txt = f"{addr_txt}, {loc_txt}"
                else:
                    direccion_txt = addr_txt or loc_txt

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                url_listing = href if href.startswith("http") else f"https://www.zonaprop.com.ar{href}"

                if not titulo and not precio_txt:
                    continue

                listings.append({
                    "titulo": titulo.strip(),
                    "precio": precio_txt.strip(),
                    "precio_num": parse_precio(precio_txt),
                    "direccion": normalize_address(direccion_txt),
                    "url": url_listing,
                    "descripcion": titulo.lower(),
                })
            except Exception:
                continue

        if len(cards) < 20:
            break

    await page.close()
    return listings
