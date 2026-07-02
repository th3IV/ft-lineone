# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Workers AI](https://img.shields.io/badge/Workers_AI-pruna/p--image--try--on-FF6F00?logo=cloudflare&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-06B6D4?logo=tailwindcss&logoColor=white)
![Cloudflare D1](https://img.shields.io/badge/D1-SQLite-F38020?logo=cloudflare&logoColor=white)
![Cloudflare R2](https://img.shields.io/badge/R2-Object_Storage-EF7B2C?logo=cloudflare&logoColor=white)
![Cloudflare Workers](https://img.shields.io/badge/Workers-Deploy-F38020?logo=cloudflare&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Descripción

**FT. THE LINE ONE** es una plataforma **B2C de Fashion Tech** que integra **Web Scraping**, **Inteligencia Artificial (LLMs)** y **Virtual Try-On (VTON)** para ofrecer una experiencia de compra de moda inteligente y personalizada.

La plataforma extrae productos desde los principales retailers de Chile, los procesa con IA, y permite a los usuarios probarse virtualmente la ropa antes de comprar.

---

## Arquitectura

Monorepo con **2 capas** que se comunican vía HTTP/JSON, todo desplegado en Cloudflare Workers:

```
Frontend React (TailwindCSS + Redux)
    └── HTTP/JSON ──► API (Cloudflare Workers Python / FastAPI + ASGI)
                          ├── Cloudflare D1 (base de datos SQL)
                          ├── Workers AI (LLM + VTON)
                          ├── Cloudflare R2 (imágenes)
                          └── Scrapers embebidos (BeautifulSoup + httpx)
                                ├── Paris (Constructor.io API + HTML fallback)
                                ├── Zara (Internal JSON API)
                                └── Maui (HTML parsing)
```

**Flujo principal:**

1. **Cron cada 5 minutos** ejecuta los scrapers embebidos → extraen productos desde retailers
2. **API** los normaliza y almacena en D1
3. **Usuario** navega en el Frontend → solicita productos desde la API
4. **Usuario** sube su foto + selecciona producto → API ejecuta VTON con Workers AI
5. **VTON** procesa con **Pruna P-Image-Try-On** (Workers AI) → resultado se retorna al Frontend
6. **LLM (Llama 3.3 70B)** genera recomendaciones personalizadas basadas en preferencias

---

## Tech Stack

| Capa | Tecnología | Versión |
|---|---|---|
| **Backend** | Cloudflare Workers + Python (Pyodide) + FastAPI (ASGI) | 3.12+ |
| **Frontend** | React + JavaScript + TailwindCSS | 18 / 3 |
| **Scrapers** | Python + BeautifulSoup + httpx | 4.x |
| **VTON** | Workers AI — Pruna P-Image-Try-On | — |
| **Base de Datos** | Cloudflare D1 (SQLite) | — |
| **Almacenamiento** | Cloudflare R2 (S3-compatible) | — |
| **IA** | Workers AI — Llama 3.3 70B Instruct (FP8 Fast) | — |
| **Autenticación** | JWT (access + refresh tokens) + PBKDF2-SHA256 | — |
| **Despliegue** | Cloudflare Workers + GitHub Actions | — |

---

## Estructura del Proyecto

```
ft-lineone/
├── workers/                         # Backend completo (Cloudflare Workers)
│   ├── src/
│   │   ├── entry.py                 # Entry point + ASGI bridge
│   │   ├── routes/
│   │   │   ├── auth.py              # Registro, login, refresh token
│   │   │   ├── users.py             # Perfil, medidas, preferencias
│   │   │   ├── products.py          # CRUD productos, búsqueda, filtros
│   │   │   ├── vton.py              # Virtual Try-On endpoints
│   │   │   ├── recommendations.py   # Recomendaciones LLM + chat de estilo
│   │   │   └── scrapers.py          # Ingesta de productos + trigger manual
│   │   ├── services/
│   │   │   ├── database.py          # D1 Database Service
│   │   │   ├── auth.py              # JWT + PBKDF2 (stdlib, sin bcrypt)
│   │   │   ├── vton.py              # Workers AI: Pruna P-Image-Try-On
│   │   │   ├── llm.py               # Workers AI: Llama 3.3 70B
│   │   │   └── r2.py                # Cloudflare R2 Storage
│   │   ├── scrapers/
│   │   │   ├── scheduler.py         # Orquestador Cron
│   │   │   ├── zara.py              # Zara (API interna /cl/es/category/)
│   │   │   ├── paris.py             # Paris (Constructor.io API + HTML)
│   │   │   └── maui.py              # Maui (HTML con BeautifulSoup)
│   │   ├── models/
│   │   │   ├── user.py              # Pydantic models
│   │   │   ├── product.py           # Pydantic models
│   │   │   └── vton_result.py       # Pydantic models
│   │   └── middleware/
│   │       └── security.py          # Auth middleware (Depends)
│   ├── schema.sql                   # D1 schema (users, products, vton_results)
│   ├── wrangler.jsonc               # Config Workers + D1 + R2 + AI + Cron
│   ├── .dev.vars                    # Variables locales de desarrollo
│   └── uv.lock                      # Lock de dependencias Python
├── frontend/                        # Aplicación React
│   ├── src/
│   │   ├── components/              # Navbar, ProductCard, ProductGrid, VirtualMirror, ModalVTON, StyleQuiz, ChatFlotante, SidebarFiltros, filtros varios
│   │   ├── pages/                   # Home, Catalog, ProductDetail, VirtualTryOn, Profile, LoginPage, RegisterPage, NotFound
│   │   ├── services/                # api.js (axios + interceptores JWT), auth.js, vton.js
│   │   ├── store/                   # Redux Toolkit (userSlice, productSlice, recommendationSlice, uiSlice)
│   │   ├── hooks/                   # useAuth
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── docs/                            # Documentación
├── .github/workflows/deploy.yml     # CI/CD
├── .env.example
├── opencode.json                    # Config opencode
└── .gitignore
```

---

## Servicios

### API (Cloudflare Workers)

API REST con FastAPI ejecutándose sobre Workers Python (ASGI bridge).

| Endpoint | Método | Descripción | Auth |
|---|---|---|---|
| `/health` | GET | Health check | No |
| `/api/v1/auth/register` | POST | Registro de usuario | No |
| `/api/v1/auth/login` | POST | Inicio de sesión | No |
| `/api/v1/auth/refresh` | POST | Renovar token | No |
| `/api/v1/users/me` | GET | Perfil del usuario | Sí |
| `/api/v1/users/profile` | PUT | Actualizar nombre/email | Sí |
| `/api/v1/users/measurements` | PUT | Actualizar medidas corporales | Sí |
| `/api/v1/users/preferences` | PUT | Actualizar preferencias de estilo | Sí |
| `/api/v1/products` | GET | Listar productos (paginado + filtros) | No |
| `/api/v1/products/{id}` | GET | Detalle del producto | No |
| `/api/v1/products/search` | GET | Buscar productos | No |
| `/api/v1/products/store/{store}` | GET | Productos por tienda | No |
| `/api/v1/products` | POST | Crear producto (admin) | Sí |
| `/api/v1/recommendations` | GET | Recomendaciones IA personalizadas | Sí |
| `/api/v1/recommendations/chat` | POST | Chat asesor de imagen IA | No |
| `/api/v1/vton/try-on` | POST | Virtual Try-On (retorna imagen binaria) | Sí |
| `/api/v1/vton/result/{id}` | GET | Metadatos de resultado VTON | Sí |
| `/api/v1/vton/history` | GET | Historial VTON del usuario | Sí |
| `/api/v1/scrapers/ingest` | POST | Ingestar producto desde scraper | No |
| `/api/v1/scrapers/ingest/batch` | POST | Ingestar lote de productos | No |
| `/api/v1/scrapers/run` | POST | Ejecutar todos los scrapers manualmente | Sí |
| `/api/v1/scrapers/run/{store}` | POST | Ejecutar scraper de una tienda | Sí |
| `/api/v1/scrapers/debug/{store}` | GET | Debug de scraper por tienda | No |

### Frontend (`:3000`)

Aplicación React 18 con:
- **Redux Toolkit** — 4 slices (user, products, recommendations, ui)
- **React Router v6** — 7 páginas (Home, Catalog, ProductDetail, VirtualTryOn, Profile, Login, Register)
- **TailwindCSS v3** — Diseño responsivo con animaciones Framer Motion
- **Axios** — Cliente HTTP con interceptores JWT (token en localStorage)
- **react-dropzone** — Subida de fotos para VTON
- **lucide-react** — Iconografía

### Scrapers (embebidos en Workers)

Módulos de scraping para retailers chilenos, ejecutados vía Cron cada 5 minutos.

| Scraper | Tienda | Método |
|---|---|---|
| `ZaraScraper` | Zara (zara.com/cl) | API JSON interna (`/category/{id}/products?ajax=true`) |
| `ParisScraper` | Paris (paris.cl) | Constructor.io Search API + HTML fallback |
| `MauiScraper` | Maui (mauiandsons.cl) | HTML parsing con BeautifulSoup |

Cada scraper se ejecuta con rate limiting (1.5-3s entre requests) y los productos se ingieren vía endpoint interno `/scrapers/ingest` con deduplicación por `external_id`.

### VTON

Servicio de Virtual Try-On integrado directamente en la API Workers. Usa **Workers AI** con el modelo `pruna/p-image-try-on`.

1. Recibe la foto del usuario + product_id (multipart)
2. Sube la foto a Cloudflare R2
3. Llama a Workers AI con el modelo Pruna P-Image-Try-On
4. Retorna la imagen resultante como binario (JPEG)
5. Guarda metadatos del resultado en D1

---

## Getting Started

### Prerrequisitos

- Node.js 18+
- Cuenta Cloudflare (para D1, R2, Workers AI)
- Wrangler CLI (`npm install -g wrangler`)

### Workers (Backend)

```bash
# Desarrollo local
cd workers
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

Las variables de Workers se configuran via `wrangler secret put` o archivo `.dev.vars`:

| Variable | Descripción |
|---|---|
| `JWT_SECRET` | Clave secreta para firmar JWTs |
| `JWT_ALGORITHM` | Algoritmo (HS256) |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) |
| `REACT_APP_API_URL` | URL base de la API para el frontend |

**Bindings (no requieren API key — se configuran en wrangler.jsonc):**
- `DB` → Cloudflare D1 database
- `R2` → Cloudflare R2 bucket
- `AI` → Cloudflare Workers AI

---

## Deployment

### Cloudflare Workers (actual)

El backend se despliega como Workers Python:

```bash
cd workers
wrangler deploy
```

Configuración declarativa en `wrangler.jsonc` con:
- D1 database binding
- R2 bucket binding
- Workers AI binding
- Cron trigger (`*/5 * * * *` para scrapers)

### Frontend

El frontend es una SPA React estática que se despliega en cualquier hosting estático (Cloudflare Pages, Vercel, etc.).

### CI/CD

GitHub Actions en `.github/workflows/deploy.yml` — despliegue automático al hacer push a `main`.

---

## Roadmap

- [x] Scrapers para retailers chilenos (Zara, Paris, Maui)
- [x] API con autenticación JWT (PBKDF2-SHA256)
- [x] Virtual Try-On con Workers AI (Pruna P-Image-Try-On)
- [x] Frontend con catálogo, búsqueda, filtros y perfil de usuario
- [x] Recomendaciones IA con Llama 3.3 70B
- [ ] Pasarela de pago (Webpay / Mercado Pago)
- [ ] Prueba virtual mejorada (múltiples prendas, outfits completos)
- [ ] App móvil (React Native)
- [ ] Migración a Workers Paid (mayor cuota de CPU)

---

## Licencia

Distribuido bajo licencia MIT.
