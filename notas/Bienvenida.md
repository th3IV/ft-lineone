# FT. THE LINE ONE

Plataforma **B2C de Fashion Tech** — Web Scraping + IA + Virtual Try-On.

## Mapa de Notas

- [[Arquitectura]] — Visión general del sistema
- [[API Endpoints]] — Todos los endpoints REST
- [[Backend — Detalle Técnico]] — Clean Architecture, modelos, servicios
- [[Frontend]] — React, rutas, componentes
- [[Scrapers]] — Extracción de productos (Falabella, Ripley, Paris, Maui, Zara)
- [[VTON]] — Virtual Try-On con modelos de difusión
- [[Setup y Desarrollo]] — Cómo levantar el proyecto localmente
- [[Performance & Deuda Técnica]] — Plan de mejoras prioritarias

## Enlaces a Docs Existentes

- [[docs/architecture]]
- [[docs/api]]
- [[docs/PLAN_MEJORA_PERFORMANCE]]
- [[README]]

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + PostgreSQL/SQLite |
| Frontend | React 19 + TailwindCSS 4 |
| Scrapers | Python + BeautifulSoup |
| VTON | Diffusion Models + PyTorch + Replicate |
| IA | Gemini 2.0 Flash / LangChain |
