# Performance & Deuda Técnica

> Basado en [[docs/PLAN_MEJORA_PERFORMANCE]].

## FASE 1 — Crítico / Seguridad 🔴

- [ ] Pipeline: reemplazar validación LLM con heurísticas

## FASE 2 — Base de Datos 📈

- [ ] Batch insert en scrapers
- [ ] Fix paginación (total count incorrecto)

## FASE 3 — Scrapers 🛡️

- [ ] Parallelizar stores con `asyncio.gather`
- [ ] Retry con backoff en `_fetch_page`
- [ ] Logging estructurado
- [ ] Parser de precios duplicado → `base_scraper.py`
- [ ] Scheduler con timezone Chile

## FASE 4 — Frontend ⚡

- [ ] Code Splitting con `React.lazy()`
- [ ] Imágenes responsivas (`?w=400`)
- [ ] Eliminar Tailwind CDN duplicado
- [ ] Token refresh interceptor (auto-refresh en 401)
- [ ] Historial VTON fuera de localStorage

## FASE 5 — Async & Task Queue ⚡

- [ ] VTON async con polling (no bloquear 30-300s)
- [ ] Scraping como BackgroundTask
- [ ] Circuit breaker para LLMs

## FASE 6 — Housekeeping 🧹

- [ ] Global exception handler en FastAPI

## Top Prioritarios

1. Parallelizar scrapers
2. Imágenes responsivas
3. Fix paginación

## Enlaces

- [[docs/PLAN_MEJORA_PERFORMANCE]]
