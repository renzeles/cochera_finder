import asyncio
from .utils import parse_precio, normalize_address

BASE_URL = "https://www.argenprop.com/cocheras/belgrano/alquiler"
MAX_PAGES = 5


async def scrape_argenprop(context):
    listings = []
    page = await context.new_page()
    await page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    for page_num in range(1, MAX_PAGES + 1):
        url = BASE_URL if page_num == 1 else f"{BASE_URL}?pagina={page_num}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception:
            break

        cards = await page.query_selector_all(".card")
        if not cards:
            break

        count_before = len(listings)
        for card in cards:
            try:
                titulo_el = await card.query_selector("h2, h3, [class*='title'], [class*='titulo']")
                titulo = await titulo_el.inner_text() if titulo_el else ""

                precio_el = await card.query_selector("[class*='price'], [class*='precio']")
                precio_txt = await precio_el.inner_text() if precio_el else ""

                addr_el = await card.query_selector("[class*='address'], [class*='direccion'], [class*='location']")
                direccion_txt = await addr_el.inner_text() if addr_el else "Belgrano, CABA"

                # Card link: the whole card or a child anchor
                link_el = await card.query_selector("a[href]")
                if not link_el:
                    # Try the card's parent
                    href = await card.get_attribute("data-href") or await card.get_attribute("href") or ""
                else:
                    href = await link_el.get_attribute("href") or ""
                url_listing = href if href.startswith("http") else f"https://www.argenprop.com{href}"

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

        # No new results on this page — stop
        if len(listings) == count_before and page_num > 1:
            break

    await page.close()
    return listings
