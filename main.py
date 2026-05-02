import asyncio
import os
import sys
import webbrowser
from playwright.async_api import async_playwright

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scrapers.zonaprop import scrape_zonaprop
from scrapers.argenprop import scrape_argenprop
from scrapers.mercadolibre import scrape_mercadolibre
from scrapers.properati import scrape_properati
from geocoder import (
    geocode, load_cache, save_cache,
    is_within_caba, address_is_non_caba, resolve_reference_point,
)
from distance import haversine
from report import generate_report

SUV_KEYWORDS = [
    "suv", "camioneta", "4x4", "pickup", "alta", "doble altura",
    "1.80", "1.9m", "2m", "2.0", "2.1", "2.2",
]


async def run_scraper(name, scraper_fn, browser):
    print(f"  -> {name}...")
    try:
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="es-AR",
        )
        listings = await scraper_fn(context)
        await context.close()
        for l in listings:
            l["fuente"] = name
        print(f"     {len(listings)} cocheras")
        return listings
    except Exception as e:
        print(f"     Error en {name}: {e}")
        return []


async def main():
    print("Buscando cocheras en Las Canitas / Belgrano...")
    print("=" * 50)

    # Geocodificar punto de referencia primero
    cache = load_cache()
    print("Resolviendo punto de referencia...")
    ref_lat, ref_lon = resolve_reference_point(cache)
    print(f"  Referencia: {ref_lat:.5f}, {ref_lon:.5f} (Luis Maria Campos y Teodoro Garcia)")

    all_listings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        for name, fn in [
            ("Zonaprop", scrape_zonaprop),
            ("Argenprop", scrape_argenprop),
            ("MercadoLibre", scrape_mercadolibre),
            ("Properati", scrape_properati),
        ]:
            results = await run_scraper(name, fn, browser)
            all_listings.extend(results)
        await browser.close()

    # Dedup por URL
    seen_urls = set()
    unique = []
    for l in all_listings:
        url = l.get("url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(l)
        elif not url:
            unique.append(l)

    print(f"\nTotal scraped: {len(unique)} cocheras unicas")

    # Filtro 1: texto — descarta provincias evidentes antes de geocodificar
    before_text = len(unique)
    unique = [l for l in unique if not address_is_non_caba(l.get("direccion", ""))]
    descartadas_texto = before_text - len(unique)
    if descartadas_texto:
        print(f"  Descartadas por texto (otra provincia): {descartadas_texto}")

    # Geocodificar y calcular distancias
    print(f"Geocodificando {len(unique)} direcciones (~{len(unique)} segundos)...")

    for i, l in enumerate(unique, 1):
        addr = l.get("direccion", "").strip()
        coords = geocode(addr, cache) if addr else None

        if coords:
            if is_within_caba(coords[0], coords[1]):
                l["lat"], l["lon"] = coords
                l["distancia_m"] = int(haversine(ref_lat, ref_lon, coords[0], coords[1]))
                l["fuera_caba"] = False
            else:
                # Geocodificó pero cayó fuera de CABA
                l["lat"], l["lon"] = None, None
                l["distancia_m"] = None
                l["fuera_caba"] = True
        else:
            l["lat"], l["lon"] = None, None
            l["distancia_m"] = None
            l["fuera_caba"] = False

        text = (l.get("titulo", "") + " " + l.get("descripcion", "")).lower()
        l["apto_suv"] = any(kw in text for kw in SUV_KEYWORDS)

        if i % 10 == 0:
            print(f"  {i}/{len(unique)} procesadas...")

    save_cache(cache)

    # Filtro 2: coordenadas fuera de CABA (segunda capa)
    before_geo = len(unique)
    unique = [l for l in unique if not l.get("fuera_caba")]
    descartadas_geo = before_geo - len(unique)
    if descartadas_geo:
        print(f"  Descartadas por coordenadas fuera de CABA: {descartadas_geo}")

    # Ordenar: distancia primero (None al final), luego precio
    def sort_key(l):
        d = l.get("distancia_m") if l.get("distancia_m") is not None else 999_999
        p = l.get("precio_num") if l.get("precio_num") is not None else 999_999_999
        return (d, p)

    unique.sort(key=sort_key)

    # Generar reporte
    os.makedirs("output", exist_ok=True)
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "resultados.html"))
    generate_report(unique, output_path, ref_lat=ref_lat, ref_lon=ref_lon)

    dentro = [l for l in unique if l.get("distancia_m") is not None and l["distancia_m"] <= 1000]
    suv_ok = [l for l in unique if l.get("apto_suv")]

    print("\n" + "=" * 50)
    print(f"LISTO: {output_path}")
    print(f"  {len(unique)} cocheras en CABA")
    print(f"  {len(dentro)} dentro de 1 km")
    print(f"  {len(suv_ok)} mencionan SUV / doble altura")
    print("=" * 50)

    webbrowser.open(f"file:///{output_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    asyncio.run(main())
