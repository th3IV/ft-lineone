# Scrapers — Extracción de Productos

> Servicio Python en `:8001`. Extrae productos de retailers chilenos con BeautifulSoup.

## Retailers Soportados

| Scraper | Store | URL Base |
|---------|-------|----------|
| `FalabellaScraper` | falabella | falabella.com |
| `RipleyScraper` | ripley | ripley.com |
| `ParisScraper` | paris | paris.cl |
| `MauiScraper` | maui | maui.cl |
| `ZaraScraper` | zara | zara.com |

## Jerarquía

```
BaseScraper (ABC)
├── FalabellaScraper
├── RipleyScraper
├── ParisScraper
├── MauiScraper
└── ZaraScraper
```

## Métodos Abstractos (BaseScraper)

- `scrape(category, max_items)` → List[ProductDTO]
- `parse_product(html, category)` → ProductDTO
- `normalize_price(price_str)` → float (heredado)
- `_build_mock_products(mock_data, ...)` → List[ProductDTO]

## Mock Data

Cada scraper tiene `MOCK_DATA` y `_generate_mock_data()` como fallback cuando la petición HTTP falla. Los datos mock incluyen productos de ejemplo con precios en CLP.

## ProductDTO

```python
external_id: str
store: str
name: str
description: str
price: float
currency: str         # CLP
original_url: str
image_urls: list[str]
category: str
sizes: list[str]
colors: list[str]
availability: bool
```

## Endpoint de Ingesta

Los scrapers envían datos al backend via:

```
POST /api/v1/scrapers/ingest
```

El backend hace upsert del producto en la base de datos.

## Archivos Clave

- `scrapers/scrapers/base_scraper.py`
- `scrapers/scrapers/falabella_scraper.py`
- `scrapers/scrapers/ripley_scraper.py`
- `scrapers/scrapers/paris_scraper.py`
- `scrapers/scrapers/zara_scraper.py`
- `scrapers/models/product_dto.py`
- `scrapers/pipeline/orchestrator.py`

## Enlaces

- [[Arquitectura]]
- [[API Endpoints]]
