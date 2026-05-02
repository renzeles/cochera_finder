import asyncio
from .utils import parse_precio, normalize_address

BASE_URL = "https://www.properati.com.ar/s/belgrano/cochera/alquiler/"
MAX_PAGES = 5


async def scrape_properati(context):
    listings = []
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    for page_num in range(1, MAX_PAGES + 1):
        url = BASE_URL if page_num == 1 else f"{BASE_URL}pagina-{page_num}/"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception:
            break

        cards = await page.query_selector_all("article")
        if not cards:
            break

        count_before = len(listings)
        for card in cards:
            try:
                titulo_el = await card.query_selector("a[class*='title'], [class*='title'] a, h2 a, h3 a")
                titulo = await titulo_el.inner_text() if titulo_el else ""

                precio_el = await card.query_selector("[class*='price'], [class*='precio']")
                precio_txt = await precio_el.inner_text() if precio_el else ""

                loc_el = await card.query_selector("[class*='location'], [class*='address'], [class*='ubicacion']")
                direccion_txt = await loc_el.inner_text() if loc_el else ""

                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                url_listing = href if href.startswith("http") else f"https://www.properati.com.ar{href}"

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

        if len(listings) == count_before and page_num > 1:
            break

    await page.close()
    return listings
