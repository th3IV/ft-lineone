import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scrapers"))

import httpx

from scrapers.zara_scraper import ZaraScraper

API_URL = os.getenv("API_URL", "http://localhost:8000/scrapers")

CATEGORIES = [
    "mujer", "hombre", "nino", "zapatos",
    "bolsos", "vestidos", "chaquetas",
]

def main():
    scraper = ZaraScraper()
    all_products = []

    print("Ejecutando ZaraScraper...")
    for category in CATEGORIES:
        try:
            products = scraper.scrape(category, max_items=10)
            print(f"  {category}: {len(products)} productos")
            all_products.extend(products)
        except Exception as e:
            print(f"  {category}: ERROR - {e}")

    if not all_products:
        print("No se obtuvieron productos. Saliendo.")
        return

    print(f"\nTotal productos scrapeados: {len(all_products)}")
    print("Enviando a backend...")

    payload = []
    for p in all_products:
        payload.append({
            "external_id": p.external_id,
            "store": p.store,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "currency": p.currency,
            "original_url": p.original_url,
            "image_urls": p.image_urls,
            "category": p.category,
            "sizes": p.sizes,
            "colors": p.colors,
            "availability": p.availability,
        })

    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{API_URL}/ingest/batch", json={"products": payload})
        if response.status_code == 200:
            data = response.json()
            ok = sum(1 for r in data["results"] if r["status"] == "ok")
            err = sum(1 for r in data["results"] if r["status"] == "error")
            print(f"Ingesta completada: {ok} OK, {err} errores")
            for r in data["results"]:
                if r["status"] == "error":
                    print(f"  Error: {r['external_id']} - {r['detail']}")
        else:
            print(f"Error en ingesta: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
