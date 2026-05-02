import re


def parse_precio(text):
    """Extract numeric value from price strings like '$ 150.000' or 'USD 500'."""
    if not text:
        return None
    cleaned = text.replace(",", "").replace("\xa0", "")
    nums = re.findall(r"\d[\d.]*", cleaned)
    if not nums:
        return None
    num_str = max(nums, key=len)
    try:
        return int(num_str.replace(".", ""))
    except ValueError:
        return None


def normalize_address(raw, fallback_zone="Belgrano, CABA"):
    """Return a clean address string suitable for geocoding."""
    if not raw or not raw.strip():
        return fallback_zone
    raw = raw.strip()
    # Remove common noise tokens
    raw = re.sub(r"\b(al|entre|y|esq\.?|esquina)\b", " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s{2,}", " ", raw).strip()
    if not any(c.isalpha() for c in raw):
        return fallback_zone
    return raw
