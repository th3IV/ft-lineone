# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Astro](https://img.shields.io/badge/Astro-7-FF5D01?logo=astro&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4-06B6D4?logo=tailwindcss&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-Workers+D1+R2+Queues+Vectorize+KV-F38020?logo=cloudflare&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Descripcion

**FT. THE LINE ONE** ([thelineone.com](https://thelineone.com)) es una plataforma **B2C de Fashion Tech** que integra **Web Scraping**, **Inteligencia Artificial (LLMs + RAG)** y **Virtual Try-On (VTON)** para ofrecer una experiencia de compra de moda inteligente y personalizada.

La plataforma extrae productos desde los principales retailers de Chile, los indexa semánticamente con Vectorize, y permite a los usuarios probarse virtualmente la ropa antes de comprar.

---

## Stack

| Capa | Tecnologia | Detalle |
|---|---|---|
| Frontend | Astro 7 + React 19 + TailwindCSS 4 + Redux Toolkit | SSR / Islands architecture desplegado en Cloudflare Pages |
| API | Cloudflare Workers Python + FastAPI (ASGI) | Pyodide runtime en el edge global — API v2.0.0 con docs OpenAPI |
| Database | Cloudflare D1 (SQLite) | `ft-lineone-db` con migraciones versionadas |
| Storage | Cloudflare R2 (S3-compatible, $0 egress) | `r2-thelineone01` (avatares/VTON), `catalogo`, `vton-temp` |
| Cache | Cloudflare KV | `PREMIUM_KV` — cache de estado premium (TTL 24h) con fallback a D1 |
| Queues | Cloudflare Queues | `scraper-jobs` + DLQ `scraper-jobs-dlq` (consumo directo en `entry.py`) |
| Vector Search | Cloudflare Vectorize + BGE-M3 | `ft-lineone-catalog` para recomendaciones RAG |
| LLM & Vision | Cloudflare Workers AI + Moondream | Llama 4 Scout, DeepSeek R1, Moondream visión |
| VTON | YouCam AI Clothes V3.0 | Virtual try-on external API con polling automatizado |
| Payments | Transbank WebPay Plus REST API | CLP 4,990/mes premium |
| Auth | JWT (access + refresh) + PBKDF2-SHA256 | Rate-limited login/register + revocación en D1 |
| Cron | Cloudflare Native Cron Triggers | Scrapers `*/5 * * * *` + VTON polling `*/2 * * * *` (ver `wrangler.jsonc`) |
| Observabilidad | Structured JSON logging | Request IDs (`X-Request-ID`) + logging de eventos por request/cron/queue |
| CI/CD | GitHub Actions | pytest gate + build + type-check frontend + deploy |

---

## Arquitectura

```text
Frontend Astro 7 / React 19 (TailwindCSS 4 + Redux)
    └── HTTP/JSON ──► API (Cloudflare Workers Python / FastAPI + ASGI, v2.0.0)
                          ├── Cloudflare D1 (base de datos SQL)
                          ├── Cloudflare KV (cache estado premium)
                          ├── Cloudflare Queues (scraper-jobs + DLQ)
                          ├── Cloudflare Vectorize (RAG semántico BGE-M3)
                          ├── Workers AI (Llama 4 Scout + Moondream)
                          ├── Cloudflare R2 (imágenes perfil, VTON, catálogo)
                          ├── YouCam API (Virtual Try-On)
                          ├── Transbank WebPay (pagos CLP)
                          └── Scrapers consumidos vía Default.queue() en entry.py
                                ├── Zara (Internal JSON API)
                                ├── Maui & Sons (GraphQL Magento)
                                ├── Falabella (SSR JSON)
                                ├── H&M (VTEX catalog system)
                                └── Fashion Park (Shopify JSON)
                                (Paris y Ripley pausados en espera de afiliados)
```

**Notas de arquitectura:**

- Los mensajes de `scraper-jobs` se procesan **directamente** en `entry.py` (`Default.queue()`): ack en éxito, `retry()` con backoff exponencial (30s × 2^n, tope 12h) en fallo, DLQ tras 3 reintentos.
- El Durable Object `ScraperWorkerEntrypoint` (`durable_objects/scraper_worker.py`) está **DEPRECATED** — se conserva solo por compatibilidad con el binding existente.
- El chat de estilo soporta **streaming SSE** (`/api/v1/recommendations/chat/stream`); el entry point hace passthrough del stream sin buffering.
- CORS estricto: orígenes no permitidos reciben **403** (no solo falta de headers). Patrón `*.ft-lineone.pages.dev` admitido; localhost solo en dev.

**Flujo VTON (YouCam):**

1. Usuario sube foto + selecciona producto
2. API valida imagen (magic bytes + 8MB max)
3. Foto de usuario se sube a freeimage.host (URL publica)
4. Foto de prenda se obtiene del catalogo
5. YouCam recibe ambas URL y procesa el try-on
6. Webhook notifica cuando termina (fallback: polling cada 2m vía cron)
7. Resultado se persiste en R2 (evita URLs expiradas de freeimage.host) y se retorna al Frontend

---

## Freemium

| Plan | VTON/dia | LLM/dia | Precio |
|------|----------|---------|--------|
| Free | 5 | 5 | Gratis |
| Premium | Ilimitado | Ilimitado | CLP 4,990/mes |

- Limites unificados en `services/config.py` — cambiar una vez, todas las rutas se actualizan
- Estado premium cacheado en KV (`kv_premium.py`, TTL 24h) con invalidación al cambiar de plan y fallback a D1
- Checkout via Transbank WebPay (tarjeta de prueba: 4051885600446623)

---

## Seguridad

| Feature | Implementacion |
|---------|---------------|
| Rate limiting | Login (20/IP, 10/email), Register (5/IP/hora) |
| Token revocation | Logout via D1 `revoked_tokens` table |
| RBAC | `require_admin` en rutas admin/debug/scrapers (`ADMIN_EMAILS` en vars) |
| CORS | Orígenes no permitidos → 403; localhost solo en dev |
| Webhook fail-closed | `YOUCAM_WEBHOOK_FAIL_CLOSED = True` |
| Error sanitization | `safe_error_message()` oculta detalles internos en prod |
| Image validation | Magic bytes + 8MB en uploads VTON y profile-image |
| IDOR protection | Ownership check en `/image/{vton_id}` |
| Atomic usage | `try_increment_usage()` previene TOCTOU races |
| Atomic refund | `refund_vton_usage()` previene double-refund |
| Observabilidad | JSON logs estructurados + `X-Request-ID` en cada response |

---

## Endpoints API

Documentación interactiva disponible en `/docs` (Swagger) y `/redoc` una vez desplegado el worker.

| Endpoint | Metodo | Descripcion | Auth |
|----------|--------|-------------|------|
| `/health` | GET | Health check (versión, runtime) | No |
| `/api/v1/auth/register` | POST | Registro | No |
| `/api/v1/auth/login` | POST | Login | No |
| `/api/v1/auth/refresh` | POST | Renovar token | No |
| `/api/v1/auth/logout` | POST | Logout (revoca token) | Si |
| `/api/v1/users/me` | GET | Perfil | Si |
| `/api/v1/users/me/usage` | GET | Uso diario (VTON/LLM) | Si |
| `/api/v1/users/profile` | PUT | Actualizar perfil | Si |
| `/api/v1/users/measurements` | PUT | Medidas corporales | Si |
| `/api/v1/users/preferences` | PUT | Preferencias de estilo | Si |
| `/api/v1/users/profile-image` | POST/DEL | Imagen de perfil | Si |
| `/api/v1/users/{id}/premium` | PATCH | Activar/desactivar premium | Admin |
| `/api/v1/products` | GET | Listar productos (paginado + filtros) | No |
| `/api/v1/products/search` | GET | Buscar productos | No |
| `/api/v1/products/store/{store}` | GET | Productos por tienda | No |
| `/api/v1/products/{id}` | GET | Detalle producto | No |
| `/api/v1/recommendations` | GET | Recomendaciones IA | Si |
| `/api/v1/recommendations/chat` | POST | Chat de estilo IA | Si |
| `/api/v1/recommendations/chat/stream` | POST | Chat de estilo IA con **streaming SSE** | Si |
| `/api/v1/vton/generate` | POST | **VTON consolidado** (recomendado) | Si |
| `/api/v1/vton/start` | POST | Crear tarea VTON (por URL de imagen) | Si |
| `/api/v1/vton/status/{job_id}` | GET | Estado de tarea VTON | Si |
| `/api/v1/vton/result/{id}` | GET | Resultado VTON | Si |
| `/api/v1/vton/history` | GET | Historial VTON | Si |
| `/api/v1/vton/image/{vton_id}` | GET | Imagen resultado (ownership check) | Si |
| `/api/v1/vton/{vton_id}/persist` | POST | Persistir resultado en R2 | Si |
| `/api/v1/vton/{vton_id}` | DELETE | Eliminar resultado VTON | Si |
| `/api/v1/vton/webhook` | POST | Webhook de YouCam (fail-closed) | No |
| `/api/v1/payments/create` | POST | Crear pago Transbank | Si |
| `/api/v1/payments/confirm` | POST | Confirmar pago | Si |
| `/api/v1/payments/webhook` | POST | Webhook de pagos | No |
| `/api/v1/payments/status` | GET | Estado de pago | Si |
| `/api/v1/favorites` | GET/POST/DEL | Favoritos del usuario | Si |
| `/api/v1/favorites/check/{product_id}` | GET | Verificar si un producto es favorito | Si |
| `/api/v1/scrapers/run` | POST | Encolar scrapers activos | Admin |
| `/api/v1/scrapers/run/{store}` | POST | Encolar scraper de una tienda | Admin |
| `/api/v1/scrapers/status` | GET | Estado de última corrida y frescura por tienda | No |
| `/api/v1/scrapers/runs` | GET | Historial de corridas de scraping | No |
| `/api/v1/scrapers/reset/{store}` | POST | Resetear estado de tienda | Admin |
| `/api/v1/scrapers/ingest` (+`/batch`) | POST | Ingesta manual de productos | Admin |

> Los endpoints marcados como deprecated (`/vton/prefetch`, `/vton/try-on`, y variantes) se mantienen por compatibilidad; usa `/vton/generate`. Los endpoints `/vton/debug-*` y `/scrapers/debug/*` son de diagnóstico admin.

### Flujo VTON (frontend)

```javascript
// 1. Llamada consolidada (recomendado)
const { id } = await api.post('/vton/generate', {
  product_id: 'abc123',
  image: 'data:image/jpeg;base64,...'  // foto del usuario
});

// 2. Polling hasta completar
const result = await api.get(`/vton/result/${id}`);
// result.status: "processing" | "completed" | "failed"
// result.output_image_url: URL de la imagen resultado
```

---

## Estructura del Proyecto

```
ft-lineone/
├── workers/                         # Backend (Cloudflare Workers Python)
│   ├── src/
│   │   ├── entry.py                 # FastAPI app + CORS + queue consumer + scheduled handler + SSE bridge
│   │   ├── cron.py                  # Polling VTON (YouCam) + persistencia de resultados en R2
│   │   ├── routes/
│   │   │   ├── auth.py              # Register, login, refresh, logout
│   │   │   ├── users.py             # Perfil, medidas, preferencias, imagen de perfil, premium
│   │   │   ├── products.py          # CRUD productos, búsqueda, listado por tienda
│   │   │   ├── vton.py              # VTON (generate, start, status, result, history, webhook)
│   │   │   ├── recommendations.py   # LLM recomendaciones + chat (+ streaming SSE)
│   │   │   ├── favorites.py         # Favoritos de productos
│   │   │   ├── payments.py          # Transbank WebPay (create, confirm, webhook, status)
│   │   │   └── scrapers.py          # Status, runs, trigger, ingest, debug
│   │   ├── services/
│   │   │   ├── config.py            # Constantes compartidas (limits, thresholds)
│   │   │   ├── database.py          # D1 CRUD + atomic usage + scrape tracking
│   │   │   ├── auth.py              # JWT + PBKDF2
│   │   │   ├── kv_premium.py        # Cache KV de estado premium (TTL 24h, fallback D1)
│   │   │   ├── llm.py               # Llama 4 Scout + pre-filtrado
│   │   │   ├── catalog_rag.py       # RAG sobre catálogo con Vectorize
│   │   │   ├── vectorize.py         # Cliente Vectorize + BGE-M3
│   │   │   ├── model_router.py      # Router multi-modelo Workers AI
│   │   │   ├── moondream.py         # Análisis de prendas con Moondream visión
│   │   │   ├── youcam.py            # YouCam API client
│   │   │   ├── image_upload.py      # freeimage.host upload + circuit breaker
│   │   │   └── r2.py                # R2 storage (perfil, VTON, catálogo)
│   │   ├── scrapers/
│   │   │   ├── scheduler.py         # Orquestador cron y validaciones
│   │   │   ├── zara.py              # Zara scraper
│   │   │   ├── maui.py              # Maui & Sons scraper (GraphQL)
│   │   │   ├── falabella.py         # Falabella scraper (Next.js SSR)
│   │   │   ├── hm.py                # H&M scraper (VTEX)
│   │   │   ├── fashionpark.py       # Fashion Park scraper (Shopify)
│   │   │   ├── paris.py             # [PAUSADO] Paris scraper
│   │   │   └── ripley.py            # [PAUSADO] Ripley scraper
│   │   ├── models/                  # Modelos de dominio (product, user, vton_result)
│   │   ├── middleware/
│   │   │   ├── security.py          # Auth + CORS + rate limit + safe_error_message
│   │   │   └── usage_limit.py       # Daily VTON/LLM limits
│   │   └── durable_objects/
│   │       └── scraper_worker.py    # [DEPRECATED] Consumo de colas movido a entry.py
│   ├── tests/                       # 71 tests (pytest)
│   ├── migrations/                  # D1 migrations (versionadas)
│   ├── python_modules/              # Dependencias empaquetadas para el runtime del worker
│   ├── schema.sql                   # D1 schema consolidado
│   └── wrangler.jsonc               # Worker config (crons, queues, bindings D1/R2/KV/AI/Vectorize/DO)
├── frontend-astro/                  # Frontend de Producción (Astro 7 + React 19)
│   ├── src/
│   │   ├── pages/                   # index, catalog, chat, login, register, profile, quiz, virtual-try-on, payment/success
│   │   ├── components/              # VirtualTryOn, VirtualMirror, OnboardingQuiz, UpgradeModal + ui/
│   │   ├── store/                   # Redux Toolkit (user, product, favorites, ui)
│   │   └── styles/                  # Tailwind CSS 4
│   ├── tests/e2e/                   # E2E tests (Playwright, critical-flows.spec.ts)
│   ├── playwright.config.ts
│   ├── astro.config.mjs
│   └── package.json
├── legacy/                          # Código histórico archivado
│   └── frontend-cra/                # Frontend original React 18 SPA (CRA)
├── .github/workflows/
│   ├── ci-cd.yml                    # Pipeline principal (backend tests + frontend build + deploy)
│   ├── deploy.yml                   # Deploy backend + frontend (push a main)
│   ├── ci.yml                       # PR checks (pytest + build)
│   └── cron-scrapers.yml            # Fallback externo para scrapers
├── docs/                            # Documentación técnica (api, architecture, security, performance)
├── TEST_PLAN.md                     # Plan de testing (unit, integration, E2E)
└── opencode.md / opencode.json      # Config del agente de desarrollo
```

---

## Testing

```bash
# Backend tests (71 tests pasando)
cd workers
python -m pytest tests/ -v

# Frontend E2E (Playwright — flujos críticos)
cd frontend-astro
npx playwright test

# Frontend build check
cd frontend-astro
npm install
npm run build
```

CI: GitHub Actions ejecuta `pytest` + build (y type-check no bloqueante del frontend) antes de cada deploy.

---

## Getting Started

### Prerequisitos

- Python 3.12+ (CI usa 3.13)
- Node.js 22.12+
- Wrangler CLI (`npm install -g wrangler`)

### Backend

```bash
cd workers
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
wrangler dev --test-scheduled
```

### Frontend

```bash
cd frontend-astro
npm install
npm run dev
```

### Deployment

```bash
# Backend
cd workers && wrangler deploy

# Frontend
cd frontend-astro && npm run build && npx wrangler pages deploy dist --project-name ft-lineone

# Migrations D1
npx wrangler d1 migrations apply ft-lineone-db --local   # local
npx wrangler d1 migrations apply ft-lineone-db           # remoto
```

Producción: frontend en [thelineone.com](https://thelineone.com) (Cloudflare Pages, proyecto `ft-lineone`), API en `api.thelineone.com`. El pipeline `ci-cd.yml` despliega automáticamente en push a `main` tras pasar los gates de testing.

---

## Roadmap

- [x] Scrapers para retailers chilenos (Zara, Maui, Falabella, H&M, Fashion Park)
- [x] API con autenticacion JWT (PBKDF2-SHA256)
- [x] Virtual Try-On con YouCam AI V3.0
- [x] Frontend con catalogo, busqueda, filtros, quiz de estilo y perfil
- [x] Recomendaciones IA con Llama 4 Scout (+ streaming SSE)
- [x] Sistema freemium/premium con Transbank WebPay
- [x] Rate limiting + RBAC + token revocation
- [x] Image validation + error sanitization
- [x] Atomic usage tracking (TOCTOU-safe)
- [x] Consolidated VTON endpoint (`/generate`)
- [x] Cache KV de estado premium
- [x] Persistencia de resultados VTON en R2
- [x] E2E tests de flujos críticos (Playwright)
- [x] CI con pytest gate
- [ ] Tests de streaming, EdDSA JWT y Turnstile (ver `TEST_PLAN.md`)
- [ ] E2E tests en CI
- [ ] ErrorBoundary (React)
- [ ] Dark mode + semantic tokens
- [ ] Remover Durable Object deprecado de scrapers
- [ ] Migracion a Workers Paid (mayor CPU)

---

## Licencia

Distribuido bajo licencia MIT.
