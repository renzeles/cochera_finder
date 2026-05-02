import json
import time
import os
from geopy.geocoders import Nominatim

CACHE_FILE = os.path.join(os.path.dirname(__file__), "geocache.json")

CABA_BOUNDS = {
    "lat_min": -34.706,
    "lat_max": -34.524,
    "lon_min": -58.535,
    "lon_max": -58.330,
}

# Si aparece alguna de estas palabras Y no hay un marcador CABA → otra provincia
NON_CABA_KEYWORDS = [
    "mendoza", "córdoba", "cordoba", "rosario", "santa fe", "santa fé",
    "tucumán", "tucuman", "salta", "jujuy", "san luis", "san juan",
    "neuquén", "neuquen", "mar del plata", "la plata", "bahía blanca",
    "bahia blanca", "escobar", "tigre", "san isidro", "vicente lópez",
    "vicente lopez", "pilar", "moreno", "merlo", "morón", "moron",
    "lanús", "lanus", "lomas de zamora", "quilmes", "avellaneda",
    "g.b.a.", "gba", "gran buenos aires", "buenos aires interior",
    "bs.as. g.b.a", "belén de escobar", "belen de escobar",
]

# Si aparece alguna de estas, es CABA aunque contenga otras palabras (ej: calle "Mendoza")
CABA_KEYWORDS = [
    "capital federal", "ciudad autónoma", "ciudad autonoma",
    "caba", "c.a.b.a.",
]

_geolocator = Nominatim(user_agent="cochera_finder_lascanitas_v3")


def is_within_caba(lat, lon):
    return (
        CABA_BOUNDS["lat_min"] <= lat <= CABA_BOUNDS["lat_max"]
        and CABA_BOUNDS["lon_min"] <= lon <= CABA_BOUNDS["lon_max"]
    )


def address_is_non_caba(address):
    """Detecta por texto si una dirección pertenece a otra provincia."""
    if not address:
        return False
    addr_lower = address.lower()
    for kw in CABA_KEYWORDS:
        if kw in addr_lower:
            return False  # Explícitamente CABA → no filtrar
    for kw in NON_CABA_KEYWORDS:
        if kw in addr_lower:
            return True
    return False


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode(address, cache=None):
    if not address or not address.strip():
        return None
    if cache is None:
        cache = load_cache()
    key = address.strip()
    if key in cache:
        return cache[key]
    query = f"{key}, Ciudad Autónoma de Buenos Aires, Argentina"
    try:
        time.sleep(1.1)
        location = _geolocator.geocode(query, timeout=10)
        result = (location.latitude, location.longitude) if location else None
    except Exception:
        result = None
    cache[key] = result
    return result


def resolve_reference_point(cache=None):
    """Geocodifica Luis María Campos y Teodoro García dinámicamente."""
    if cache is None:
        cache = load_cache()
    key = "__REF__Luis Maria Campos y Teodoro Garcia"
    if key in cache and cache[key]:
        return tuple(cache[key])

    queries = [
        "Luis María Campos 1295, Las Cañitas, Buenos Aires, Argentina",
        "Avenida Luis María Campos y Teodoro García, Buenos Aires, Argentina",
        "Luis Maria Campos 1295, Palermo, Buenos Aires, Argentina",
    ]
    for q in queries:
        try:
            time.sleep(1.1)
            loc = _geolocator.geocode(q, timeout=10)
            if loc and is_within_caba(loc.latitude, loc.longitude):
                result = (loc.latitude, loc.longitude)
                cache[key] = list(result)
                save_cache(cache)
                return result
        except Exception:
            continue

    # Fallback: Luis María Campos al 1295, Las Cañitas
    fallback = (-34.5697, -58.4435)
    cache[key] = list(fallback)
    save_cache(cache)
    return fallback
