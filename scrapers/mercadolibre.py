import asyncio
from .utils import parse_precio, normalize_address

BASE_URL = "https://inmuebles.mercadolibre.com.ar/cocheras/alquiler/belgrano/"
MAX_PAGES = 5


async def scrape_mercadolibre(context):
    listings = []
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    offset = 1
    for _ in range(MAX_PAGES):
        url = BASE_URL if offset == 1 else f"{BASE_URL}_Desde_{offset}_NoIndex_True"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception:
            break

        cards = await page.query_selector_all("li.ui-search-layout__item")
        if not cards:
            break

        for card in cards:
            try:
                # New MercadoLibre structure uses poly-card
                titulo_el = await card.query_selector("a.poly-component__title, h3.poly-component__title-wrapper a")
                titulo = await titulo_el.inner_text() if titulo_el else ""

                # Price is in andes-money-amount with aria-label
                precio_el = await card.query_selector("span.andes-money-amount")
                precio_txt = ""
                if precio_el:
                    aria = await precio_el.get_attribute("aria-label")
                    precio_txt = aria or await precio_el.inner_text()

                loc_el = await card.query_selector("span.poly-component__location")
                direccion_txt = await loc_el.inner_text() if loc_el else "Belgrano, CABA"

                link_el = await card.query_selector("a.poly-component__title, a[href*='mercadolibre']")
                href = await link_el.get_attribute("href") if link_el else ""

                if not titulo:
                    continue

                listings.append({
                    "titulo": titulo.strip(),
                    "precio": precio_txt.strip(),
                    "precio_num": parse_precio(precio_txt),
                    "direccion": normalize_address(direccion_txt),
                    "url": href,
                    "descripcion": titulo.lower(),
                })
            except Exception:
                continue

        if len(cards) < 48:
            break
        offset += 48

    await page.close()
    return listings
