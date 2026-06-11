---
name: scrapers
description: >
  Use when working on web scrapers: adding a new retailer, modifying parsing
  logic, or running the scraping pipeline. Covers BeautifulSoup scrapers for
  Falabella, Ripley, Paris, Maui, and Zara.
---

# Scrapers Skill

Módulos de scraping con BeautifulSoup para extraer productos desde retailers chilenos (Falabella, Ripley, Paris, Maui, Zara).

## Estructura
```
scrapers/
├── scrapers/
│   ├── base_scraper.py     # Clase abstracta base
│   ├── falabella.py
│   ├── ripley.py
│   ├── paris.py
│   ├── maui.py
│   └── zara.py
├── models/
│   └── product_dto.py
├── pipeline/
│   └── orchestrator.py
├── tests/
├── requirements.txt
└── Dockerfile
```

## Setup
```powershell
cd scrapers
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python pipeline/orchestrator.py
```

## Convenciones

### Nuevo scraper
1. Heredar de `BaseScraper` e implementar:
   - `fetch_products()` — obtener HTML de la tienda
   - `parse_product()` — extraer datos del HTML
   - `normalize_data()` — estandarizar formato
2. Registrar en `pipeline/orchestrator.py`

### Formato de salida
Cada scraper retorna productos con:
```python
{
    "external_id": str, "store": str, "name": str,
    "description": str, "price": float, "currency": str,
    "image_url": str, "category": str,
    "sizes": list[str], "colors": list[str],
}
```

### Buenas prácticas
- Usar `time.sleep()` entre requests para evitar bloqueos
- Manejar `HTTPError` y `ConnectionError`
- LOG cada paso del scraping
- Headers con User-Agent realista
