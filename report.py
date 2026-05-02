import os
import json
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def generate_report(listings, output_path, ref_lat=-34.5697, ref_lon=-58.4435):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")

    markers = [
        {
            "lat": l["lat"],
            "lon": l["lon"],
            "titulo": l.get("titulo", ""),
            "precio": l.get("precio", ""),
            "distancia_m": l.get("distancia_m"),
            "url": l.get("url", ""),
            "fuente": l.get("fuente", ""),
            "apto_suv": l.get("apto_suv", False),
        }
        for l in listings
        if l.get("lat") and l.get("lon")
    ]

    html = template.render(
        listings=listings,
        markers_json=json.dumps(markers, ensure_ascii=False),
        total=len(listings),
        dentro_1km=sum(1 for l in listings if l.get("distancia_m") is not None and l["distancia_m"] <= 1000),
        ref_lat=ref_lat,
        ref_lon=ref_lon,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
