# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-06B6D4?logo=tailwindcss&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-Workers+D1+R2-F38020?logo=cloudflare&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Descripcion

**FT. THE LINE ONE** es una plataforma **B2C de Fashion Tech** que integra **Web Scraping**, **Inteligencia Artificial (LLMs)** y **Virtual Try-On (VTON)** para ofrecer una experiencia de compra de moda inteligente y personalizada.

La plataforma extrae productos desde los principales retailers de Chile, los procesa con IA, y permite a los usuarios probarse virtualmente la ropa antes de comprar.

---

## Stack

| Capa | Tecnologia | Detalle |
|------|-----------|---------|
| Frontend | React 18 + Redux Toolkit + TailwindCSS + Framer Motion | SPA con code splitting |
| API | Cloudflare Workers Python + FastAPI (ASGI) | Pyodide runtime |
| Database | Cloudflare D1 (SQLite) | `ft-lineone-db` |
| Storage | Cloudflare R2 (S3-compatible) | `r2-thelineone01` |
| LLM | Cloudflare Workers AI — Llama 4 Scout | Recomendaciones + chat |
| VTON | YouCam AI Clothes V3.0 | Virtual try-on external API |
| Payments | Transbank WebPay Plus REST API | CLP 4,990/mes premium |
| Auth | JWT (access + refresh) + PBKDF2-SHA256 | Rate-limited login/register |
| Cron | `*/45 * * * *` | Scrapers + VTON polling + cleanup |
| CI/CD | GitHub Actions | pytest gate + deploy |

---

## Arquitectura

```text
Frontend React (TailwindCSS + Redux)
    └── HTTP/JSON ──► API (Cloudflare Workers Python / FastAPI + ASGI)
                          ├── Cloudflare D1 (base de datos SQL)
                          ├── Workers AI (Llama 4 Scout)
                          ├── Cloudflare R2 (imagenes VTON)
                          ├── YouCam API (Virtual Try-On)
                          ├── Transbank WebPay (pagos)
                          └── Scrapers embebidos (BeautifulSoup + httpx)
                                ├── Paris (Constructor.io API + HTML fallback)
                                ├── Zara (Internal JSON API)
                                └── Maui (HTML parsing)
```

**Flujo VTON (YouCam):**

1. Usuario sube foto + selecciona producto
2. API valida imagen (magic bytes + 8MB max)
3. Foto de usuario se sube a freeimage.host (URL publica)
4. Foto de prenda se obtiene del catalogo
5. YouCam recibe ambas URL y procesa el try-on
6. Webhook notifica cuando termina (fallback: polling cada 10s)
7. Resultado se almacena en R2 y se retorna al Frontend

---

## Freemium

| Plan | VTON/dia | LLM/dia | Precio |
|------|----------|---------|--------|
| Free | 5 | 5 | Gratis |
| Premium | Ilimitado | Ilimitado | CLP 4,990/mes |

- Limites unificados en `services/config.py` — cambiar una vez, todas las rutas se actualizan
- Checkout via Transbank WebPay (tarjeta de prueba: 4051885600446623)

---

## Seguridad

| Feature | Implementacion |
|---------|---------------|
| Rate limiting | Login (20/IP, 10/email), Register (5/IP/hora) |
| Token revocation | Logout via D1 `revoked_tokens` table |
| RBAC | `require_admin` en rutas admin/debug/scrapers |
| CORS | Dependiente de `ENVIRONMENT` — localhost solo en dev |
| Webhook fail-closed | `YOUCAM_WEBHOOK_FAIL_CLOSED = True` |
| Error sanitization | `safe_error_message()` oculta detalles internos en prod |
| Image validation | Magic bytes + 8MB en uploads VTON |
| IDOR protection | Ownership check en `/image/{vton_id}` |
| Atomic usage | `try_increment_usage()` previene TOCTOU races |
| Atomic refund | `refund_vton_usage()` previene double-refund |

---

## Endpoints API

| Endpoint | Metodo | Descripcion | Auth |
|----------|--------|-------------|------|
| `/health` | GET | Health check | No |
| `/api/v1/auth/register` | POST | Registro | No |
| `/api/v1/auth/login` | POST | Login | No |
| `/api/v1/auth/refresh` | POST | Renovar token | No |
| `/api/v1/auth/logout` | POST | Logout (revoca token) | Si |
| `/api/v1/users/me` | GET | Perfil | Si |
| `/api/v1/users/profile` | PUT | Actualizar perfil | Si |
| `/api/v1/users/preferences` | PUT | Preferencias de estilo | Si |
| `/api/v1/users/premium` | GET | Estado premium | Si |
| `/api/v1/products` | GET | Listar productos (paginado + filtros) | No |
| `/api/v1/products/{id}` | GET | Detalle producto | No |
| `/api/v1/products/search` | GET | Buscar productos | No |
| `/api/v1/recommendations` | GET | Recomendaciones IA | Si |
| `/api/v1/recommendations/chat` | POST | Chat de estilo IA | Si |
| `/api/v1/vton/generate` | POST | **VTON consolidado** (nuevo) | Si |
| `/api/v1/vton/prefetch` | POST | [DEPRECATED] Pre-upload foto | Si |
| `/api/v1/vton/try-on` | POST | [DEPRECATED] Crear tarea VTON | Si |
| `/api/v1/vton/result/{id}` | GET | Resultado VTON | Si |
| `/api/v1/vton/history` | GET | Historial VTON | Si |
| `/api/v1/payments/create` | POST | Crear pago Transbank | Si |
| `/api/v1/payments/confirm` | POST | Confirmar pago | Si |
| `/api/v1/scrapers/run` | POST | Ejecutar scrapers | Admin |

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
│   │   ├── entry.py                 # FastAPI app + CORS + cron
│   │   ├── routes/
│   │   │   ├── auth.py              # Register, login, refresh, logout
│   │   │   ├── users.py             # Perfil, preferencias, premium
│   │   │   ├── products.py          # CRUD productos
│   │   │   ├── vton.py              # VTON (generate, result, history, webhook)
│   │   │   ├── recommendations.py   # LLM recomendaciones + chat
│   │   │   ├── payments.py          # Transbank WebPay
│   │   │   └── scrapers.py          # Trigger scrapers
│   │   ├── services/
│   │   │   ├── config.py            # Constantes compartidas (limits, thresholds)
│   │   │   ├── database.py          # D1 CRUD + atomic usage
│   │   │   ├── auth.py              # JWT + PBKDF2
│   │   │   ├── llm.py               # Llama 4 Scout + pre-filtrado
│   │   │   ├── youcam.py            # YouCam API client
│   │   │   ├── image_upload.py      # freeimage.host upload + circuit breaker
│   │   │   └── r2.py                # R2 storage
│   │   ├── scrapers/
│   │   │   ├── scheduler.py         # Orquestador cron
│   │   │   ├── zara.py              # Zara scraper
│   │   │   ├── paris.py             # Paris scraper
│   │   │   └── maui.py              # Maui scraper
│   │   └── middleware/
│   │       ├── security.py          # Auth + CORS + rate limit + safe_error_message
│   │       └── usage_limit.py       # Daily VTON/LLM limits
│   ├── tests/                       # 55 tests (pytest)
│   ├── migrations/                  # D1 migrations
│   ├── schema.sql                   # D1 schema
│   └── wrangler.jsonc               # Worker config
├── frontend/                        # React SPA
│   ├── src/
│   │   ├── pages/                   # Home, Catalog, ProductDetail, VTON, Profile, Login, Register
│   │   ├── components/              # UI components
│   │   ├── store/                   # Redux (user, products, recommendations, ui)
│   │   ├── hooks/                   # useAuth, useFeatureGate
│   │   └── services/                # api.js, auth.js, vton.js, payments.js
│   └── package.json
├── .github/workflows/
│   ├── deploy.yml                   # CI/CD (pytest gate + deploy)
│   └── ci.yml                       # PR checks (pytest + build)
└── opencode.md                      # AI agent context file
```

---

## Testing

```bash
# Backend tests
cd workers
python -m pytest tests/ -v

# Frontend build check
cd frontend
npm ci
npm run build
```

**55 tests** cubriendo: auth (JWT + hashing), config (limits + thresholds), security (CORS + error sanitization), LLM prompts, middleware helpers, entry point.

---

## Getting Started

### Prerequisitos

- Python 3.12+
- Node.js 18+
- Wrangler CLI (`npm install -g wrangler`)

### Backend

```bash
cd workers
pip install -r requirements.txt
wrangler dev
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Abrir en `http://localhost:3000`.

### Variables de Entorno

**Wrangler Secrets** (via `wrangler secret put`):

| Secret | Descripcion |
|--------|-------------|
| `JWT_SECRET` | HMAC-SHA256 signing key |
| `TRANSBANK_API_KEY` | Transbank API secret |
| `YOUCAM_API_KEY` | YouCam Bearer token |
| `YOUCAM_WEBHOOK_SECRET` | YouCam webhook HMAC secret |

**Wrangler Vars** (en `wrangler.jsonc`):

| Var | Valor |
|-----|-------|
| `JWT_ALGORITHM` | `HS256` |
| `CORS_ORIGINS` | `thelineone.com, www.thelineone.com, localhost:3000` |
| `TRANSBANK_COMMERCE_CODE` | `597055555532` (sandbox) |
| `TRANSBANK_BASE_URL` | `https://webpay3gint.transbank.cl` |
| `ENVIRONMENT` | `production` |

**Bindings** (en `wrangler.jsonc`):
- `DB` → Cloudflare D1 (`ft-lineone-db`)
- `R2` → Cloudflare R2 (`r2-thelineone01`)
- `AI` → Cloudflare Workers AI

---

## Deployment

```bash
# Backend
cd workers && wrangler deploy

# Frontend
cd frontend && npm run build && npx wrangler pages deploy dist --project-name ft-lineone

# Migration (one-time)
npx wrangler d1 execute ft-lineone-db --file=./migrations/0001_add_gender_and_indexes.sql
```

CI/CD: GitHub Actions ejecuta `pytest` antes de cada deploy.

---

## Roadmap

- [x] Scrapers para retailers chilenos (Zara, Paris, Maui)
- [x] API con autenticacion JWT (PBKDF2-SHA256)
- [x] Virtual Try-On con YouCam AI V3.0
- [x] Frontend con catalogo, busqueda, filtros y perfil
- [x] Recomendaciones IA con Llama 4 Scout
- [x] Sistema freemium/premium con Transbank WebPay
- [x] Rate limiting + RBAC + token revocation
- [x] Image validation + error sanitization
- [x] Atomic usage tracking (TOCTOU-safe)
- [x] Consolidated VTON endpoint (`/generate`)
- [x] CI con pytest gate
- [ ] E2E tests (Playwright)
- [ ] ErrorBoundary (React)
- [ ] Dark mode + semantic tokens
- [ ] Migracion a Workers Paid (mayor CPU)

---

## Licencia

Distribuido bajo licencia MIT.
