# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-06B6D4?logo=tailwindcss&logoColor=tailwindcss)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7-47A248?logo=mongodb&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-GPT4-1C3C3C?logo=langchain&logoColor=white)
![Render](https://img.shields.io/badge/Render-Deploy-46E3B7?logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Descripción

**FT. THE LINE ONE** es una plataforma **B2C de Fashion Tech** que integra **Web Scraping**, **Inteligencia Artificial (LLMs)** y **Virtual Try-On (VTON)** para ofrecer una experiencia de compra de moda inteligente y personalizada.

La plataforma extrae productos en tiempo real desde los principales retailers de Chile, los procesa con IA, y permite a los usuarios probarse virtualmente la ropa antes de comprar.

---

## Arquitectura

Monorepo estructurado en **4 microservicios** que se comunican vía HTTP/JSON:

```
Frontend React (TailwindCSS + Redux)
    ├── HTTP/JSON ──► Backend API (FastAPI)
    │                     ├── PostgreSQL (datos estructurados)
    │                     ├── MongoDB (datos no estructurados / scraping)
    │                     ├── Cloudflare R2 (imágenes)
    │                     └── Scrapers (BeautifulSoup)
    │                           ├── Falabella
    │                           ├── Ripley
    │                           ├── Paris
    │                           ├── Maui
    │                           ├── Zara
    │                           └── etc.
    └── HTTP/JSON ──► VTON Service (FastAPI + Replicate)
                          └── Cloudflare R2 (output)
```

**Flujo principal:**
1. **Scrapers** extraen productos desde los retailers → los envían al backend
2. **Backend** los procesa, normaliza, valida con LLM y almacena (PostgreSQL + MongoDB)
3. **Usuario** navega en el Frontend → solicita productos desde la API
4. **Usuario** sube su foto + selecciona producto → Backend envía al servicio **VTON**
5. **VTON** procesa con IDM-VTON (Replicate API) → resultado se guarda en R2 → se muestra en Frontend
6. **LLM (GPT-4)** genera recomendaciones personalizadas basadas en preferencias e historial

---

## Tech Stack

| Capa | Tecnología | Versión |
|---|---|---|
| **Backend** | FastAPI + Python | 3.12+ / 0.115 |
| **Frontend** | React + JavaScript + TailwindCSS | 18 / 3 |
| **Scrapers** | Python + BeautifulSoup + requests | 4.x |
| **VTON** | FastAPI + Replicate API (IDM-VTON) | — |
| **Base de Datos** | PostgreSQL + MongoDB | 16 / 7 |
| **Almacenamiento** | Cloudflare R2 (S3-compatible) | — |
| **IA** | LangChain + GPT-4 + Replicate | — |
| **Autenticación** | JWT (access + refresh tokens) + bcrypt | — |
| **Cache / Queue** | Redis + Celery | 7 / 5.4 |
| **Despliegue** | Render + GitHub Actions | — |

---

## Estructura del Proyecto

```
ft-lineone/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/        # FastAPI endpoints
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── products.py
│   │   │   ├── recommendations.py
│   │   │   └── vton.py
│   │   ├── core/                  # Config, seguridad
│   │   ├── domain/models/         # User, Product, VTONResult, Account, Session
│   │   ├── application/
│   │   │   ├── services/          # Lógica de negocio
│   │   │   └── orchestrator/      # Pipelines multi-paso
│   │   ├── infrastructure/
│   │   │   ├── persistence/       # PostgreSQL (SQLAlchemy) + MongoDB (Motor)
│   │   │   └── external_services/ # LLMClient, VTONClient, ScraperClient
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/            # Navbar, ProductCard, ProductGrid, VirtualMirror, StyleQuiz
│   │   ├── pages/                 # Home, Catalog, ProductDetail, VirtualTryOn, Profile
│   │   ├── services/              # api.js, auth.js, vton.js
│   │   ├── store/                 # Redux Toolkit (user, products, recommendations)
│   │   ├── hooks/                 # useAuth
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── Dockerfile
├── scrapers/
│   ├── scrapers/                  # BaseScraper + Falabella, Ripley, Paris, Maui, Zara
│   ├── models/                    # ProductDTO
│   ├── pipeline/                  # DataNormalizer, ImageProcessor, Publisher
│   ├── requirements.txt
│   └── Dockerfile
├── vton/
│   ├── app/
│   │   ├── api/routes.py          # Endpoints de Virtual Try-On
│   │   ├── services/              # TryOnService, ReplicateClient, S3Connector, ImageProcessor
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── infra/                         # (reservado para Terraform AWS)
├── docs/
│   ├── architecture.md
│   └── api.md
├── .github/workflows/deploy.yml   # CI/CD a Render
├── render.yaml                    # Configuración de despliegue
├── .env.example
└── .gitignore
```

---

## Servicios

### Backend API (`:8000`)

API REST con FastAPI, arquitectura hexagonal (puertos y adaptadores).

| Endpoint | Método | Descripción | Auth |
|---|---|---|---|
| `/health` | GET | Health check | No |
| `/auth/register` | POST | Registro de usuario | No |
| `/auth/login` | POST | Inicio de sesión | No |
| `/auth/refresh` | POST | Renovar token | No |
| `/users/me` | GET | Perfil del usuario | Sí |
| `/users/me/measurements` | PUT | Actualizar medidas corporales | Sí |
| `/users/me/history` | GET | Historial de interacciones | Sí |
| `/products` | GET | Listar productos (paginado) | No |
| `/products/{id}` | GET | Detalle del producto | No |
| `/products/search` | GET | Buscar productos | No |
| `/products/store/{store}` | GET | Productos por tienda | No |
| `/recommendations` | GET | Recomendaciones IA | Sí |
| `/vton/try-on` | POST | Virtual Try-On | Sí |
| `/vton/result/{id}` | GET | Resultado VTON | Sí |

### Frontend (`:3000`)

Aplicación React 18 con:
- **Redux Toolkit** — 3 slices (user, products, recommendations)
- **React Router v6** — 5 páginas (Home, Catalog, ProductDetail, VirtualTryOn, Profile)
- **TailwindCSS v3** — Diseño responsivo
- **Axios** — Cliente HTTP con interceptores JWT
- **react-dropzone** — Subida de fotos para VTON
- **react-hot-toast** — Notificaciones

### Scrapers

Módulos de scraping para retailers chilenos con BeautifulSoup + requests. Cada scraper hereda de `BaseScraper` e incluye fallback con datos mock para desarrollo.

| Scraper | Tienda | URL Base |
|---|---|---|
| `FalabellaScraper` | Falabella | falabella.com |
| `RipleyScraper` | Ripley | ripley.com |
| `ParisScraper` | Paris | paris.cl |
| `MauiScraper` | Maui | maui.cl |
| `ZaraScraper` | Zara | zara.com |
| — | *y más en el futuro* | — |

Pipeline de procesamiento: `DataNormalizer` (estandariza categorías, tallas, colores, moneda) → `ImageProcessor` (redimensiona, watermarks, thumbnails) → `Publisher` (envía al backend).

### VTON Service (`:8001`)

Microservicio de Virtual Try-On que:
1. Recibe la foto del usuario + ID del producto
2. Sube la foto a Cloudflare R2
3. Llama a Replicate API con el modelo **IDM-VTON** (`cuuupid/idm-vton`)
4. Retorna la URL del resultado generado

Endpoints:
- `POST /try-on` — Solicitar try-on (multipart: user_image + product_id + user_id)
- `GET /try-on/{job_id}/status` — Estado del proceso
- `GET /try-on/{job_id}/result` — Resultado final
- `POST /try-on/{job_id}/retry` — Reintentar si falló

---

## Getting Started

### Prerrequisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL 16 (o Docker)
- MongoDB 7 (o Docker)

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate    # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Abrir en `http://localhost:3000`.

### Scrapers

```bash
cd scrapers
python -m venv venv
pip install -r requirements.txt
python -m scrapers
```

### VTON

```bash
cd vton
python -m venv venv
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `MONGODB_URL` | MongoDB connection string |
| `JWT_SECRET` | Clave secreta para JWT |
| `R2_ACCOUNT_ID` | Cloudflare R2 account ID |
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret key |
| `R2_BUCKET` | Bucket name (ft-lineone-media) |
| `R2_PUBLIC_URL` | URL pública de R2 |
| `REPLICATE_API_TOKEN` | Token de Replicate API |
| `REPLICATE_MODEL` | Modelo VTON (cuuupid/idm-vton) |
| `OPENAI_API_KEY` | OpenAI API key para LLM |
| `REACT_APP_API_URL` | URL base de la API (frontend) |

---

## Deployment

### Render (actual)

Configuración declarativa en `render.yaml` con 4 servicios:
- **ft-lineone-backend** — Web service Python (Free)
- **ft-lineone-scrapers** — Web service Python (Free)
- **ft-lineone-vton** — Web service Python (Free)
- **ft-lineone-frontend** — Static site

Base de datos: PostgreSQL + Redis (Free).

### CI/CD

GitHub Actions en `.github/workflows/deploy.yml` — despliegue automático a Render al hacer push a `main`.

---

## Estrategia de Infraestructura y Escalabilidad

Para la fase de validación y pruebas de integración, se utilizarán servicios en sus capas gratuitas (*Free Tier*) con el objetivo de garantizar un entorno de testing robusto sin incurrir en costes operativos significativos. 

Una vez que el proyecto alcance métricas de sostenibilidad, ya sea por tracción financiera o reconocimiento de usuarios, se ejecutará el plan de migración hacia la infraestructura de grado empresarial definida en `docs/architecture.md`. La transición hacia **AWS** permitirá garantizar la alta disponibilidad y la escalabilidad horizontal necesaria para el crecimiento del servicio.

| Capa Actual (Free/Demo) | Objetivo en Producción (AWS) | Beneficio de la Migración |
|---|---|---|
| **Render** (web services, PostgreSQL, Redis) | **AWS EKS** (Kubernetes) + **RDS** (PostgreSQL) + **ElastiCache** (Redis) | Orquestación de contenedores y auto-scaling |
| **Cloudflare R2** (almacenamiento S3-compatible) | **AWS S3** | Almacenamiento de objetos de alta durabilidad |
| **Replicate API** (IDM-VTON free credits) | **AWS SageMaker** / **EC2 GPU** (modelo propio) | Control total de la inferencia de modelos de difusión |
| **GitHub Actions** | **AWS CodePipeline** + **CodeBuild** | CI/CD enterprise-grade |
| — | **AWS API Gateway** | Gestión de tráfico y seguridad de la API |
| — | **AWS Lambda** | Procesamiento asíncrono y tareas programadas (cron) |

---

## Roadmap

- [x] Scrapers para retailers chilenos
- [x] Backend con autenticación JWT y arquitectura hexagonal
- [x] Virtual Try-On con Replicate API
- [x] Frontend con catálogo, búsqueda y perfil de usuario
- [x] Despliegue automatizado en Render
- [ ] Pasarela de pago (Webpay / Mercado Pago)
- [ ] Perfil de estilo con IA (cuestionario + recomendaciones)
- [ ] Prueba virtual mejorada (múltiples prendas, outfits completos)
- [ ] App móvil (React Native)
- [ ] Migración a AWS para escalabilidad horizontal
- [ ] Modelo VTON propio en SageMaker / EC2 GPU

---

## Licencia

Distribuido bajo licencia MIT.
