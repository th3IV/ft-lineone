# Plan de Ejecución — FT. THE LINE ONE Performance

> Archivo de referencia para retomar la implementación desde otra sesión.
> Creado: 2026-06-20

---

## FASE 1 — Crítico / Seguridad (Hacer YA)

| # | Tarea | Impacto | Archivos |
|---|---|---|---|---|
| 1 | **Pipeline: 3 LLM calls por producto** — validar + normalizar + imagen = 2,880 llamadas en full run | 🔴 Quota agotada | `base_scraper.py` → reemplazar validación LLM con reglas heurísticas |

- [ ] **1.1** Pipeline: LLM → heurísticas

---

## FASE 2 — Caching & Base de Datos (Alto impacto)

| # | Tarea | Impacto | Archivos |
|---|---|---|---|---|
| 5 | **Batch insert en vez de `save()` individual** — `bulk_write` con `UpdateOne` | 📈 Scraping | `repositories.py` |
| 6 | **Paginación: `find_by_store` sin total count** — `total = len(products)` es incorrecto | 🐛 Bug | `repositories.py` + `main.py` |

- [ ] **2.1** `bulk_write` en repositorios
- [ ] **2.2** Fix paginación (total count)

---

## FASE 3 — Scrapers (Medio impacto)

| # | Tarea | Impacto | Archivos |
|---|---|---|---|
| 10 | **Playwright: timeout y max-height en scroll** — si la página es infinita, nunca termina | 🛡️ Robustez | `zara_scraper.py` |
| 11 | **Parallelizar stores con `asyncio.gather`** — 6 stores secuenciales → paralelos con semáforo | ⚡ Velocidad | `pipeline.py` |
| 12 | **Retry con backoff en `_fetch_page`** — un 503 aborta toda la categoría | 🛡️ Robustez | `base_scraper.py` |
| 13 | **Logging estructurado en scrapers** — `except Exception: continue` traga errores sin registro | 📊 Debug | Todos los scrapers |
| 14 | **Parser de precios duplicado** — extraer a `base_scraper.py` | 🧹 Código | `*_scraper.py` |
| 15 | **Scheduler: usar timezone Chile** — `America/Santiago` en vez de UTC | 🐛 Bug | `scheduler.py` |

- [ ] **3.1** Playwright: timeout + max-height scroll
- [ ] **3.2** Parallelizar stores (`asyncio.gather`)
- [ ] **3.3** Retry con backoff en `_fetch_page`
- [ ] **3.4** Logging en scrapers
- [ ] **3.5** Parser precios → `base_scraper.py`
- [ ] **3.6** Scheduler: timezone Chile

---

## FASE 4 — Frontend (Alto impacto visual)

| # | Tarea | Impacto | Archivos |
|---|---|---|---|
| 16 | **Code Splitting con `React.lazy()`** — bundle único de ~130KB → rutas lazy | ⚡ Carga inicial | `App.jsx` |
| 17 | **Imágenes responsivas** — thumbnails en 200px cargan imagen full resolution | ⚡ Tiempo de carga | `ProductCard.jsx` + `?w=400` |
| 18 | **Eliminar Tailwind CDN** — duplicado con npm (versión 2.x vs 3.x) | 🐛 Bug CSS | `index.html` |
| 19 | **Token refresh interceptor** — 401 solo limpia token, no intenta refresh | 🛡️ UX | `api.js` |
| 20 | **Historial VTON fuera de localStorage** — base64 de 500KB+ agota el storage | 🐛 Bug | `VirtualTryOn.jsx` |
| 21 | **Normalizar API responses** — snake_case vs camelCase inconsistente | 🧹 Código | Redux slices |

- [ ] **4.1** Code Splitting (`React.lazy`)
- [ ] **4.2** Imágenes responsivas (`?w=400`)
- [ ] **4.3** Eliminar Tailwind CDN duplicado
- [ ] **4.4** Token refresh interceptor
- [ ] **4.5** Historial VTON → persistencia real
- [ ] **4.6** Normalizar API responses

---

## FASE 5 — Async & Task Queue (Alto impacto)

| # | Tarea | Impacto | Archivos |
|---|---|---|---|
| 22 | **VTON async con polling** — `POST /vton/try-on` espera 30-300s bloqueando | ⚡ UX | `main.py` + frontend |
| 23 | **Scraping como BackgroundTask** — no ejecutarlo inline en el request | ⚡ UX | `main.py` + `pipeline.py` |

- [ ] **5.1** VTON async con polling
- [ ] **5.2** Scraping como BackgroundTask

---

## FASE 6 — Housekeeping (Bajo impacto)

| # | Tarea | Impacto |
|---|---|---|
| 25 | Global exception handler en FastAPI | 🛡️ |

- [ ] **6.1** Global exception handler

---

## 🏆 Top 5 Recomendados para la Próxima Semana

1. **Parallelizar scrapers** — `asyncio.gather` + semáforo, reduce tiempo de 48 ops secuenciales
2. **Imágenes responsivas en frontend** — `?w=400` en thumbnails, impacto visible inmediato

---

## Progreso General

```
FASE 1: ░░░░░░░░░░  0%
FASE 2: ░░░░░░░░░░  0%
FASE 3: ░░░░░░░░░░  0%
FASE 4: ░░░░░░░░░░  0%
FASE 5: ░░░░░░░░░░  0%
FASE 6: ░░░░░░░░░░  0%
```

> Marcar con `[x]` cada tarea completada. Actualizar el progreso al final de cada sesión.
