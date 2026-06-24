# Arquitectura del Sistema

## Visión General

FT. THE LINE ONE está compuesto por **4 microservicios** que trabajan de forma orquestada para ofrecer una experiencia de moda inteligente:

| Microservicio | Tecnología | Rol |
|---|---|---|
| **Backend API** | FastAPI (Python) | Orquestación, usuarios, productos, recomendaciones, pipeline de scraping y VTON |
| **Frontend Web** | React + TailwindCSS | Interfaz de usuario B2C |
| **Scrapers** | Python + BeautifulSoup | Extracción de productos desde retailers |
| **VTON Service** | Diffusion Models + PyTorch | Virtual Try-On con IA generativa |

## Diagrama de Flujo de Datos

```
                         ┌──────────────────────────────────────────┐
                         │              Frontend React              │
                         │         (TailwindCSS + JavaScript)        │
                         └──┬───────────────────────────────┬───────┘
                            │ HTTP/JSON                    │ HTTP/JSON
                            ▼                              ▼
                    ┌────────────────┐           ┌──────────────────┐
                    │   Backend API  │◄──────────│  VTON Service    │
                    │   (FastAPI)    │           │  (PyTorch + SD)  │
                    └───┬────────────┘           └────────┬─────────┘
                        │                                 │
                        ▼                                 ▼
               ┌──────────┐                      ┌────────────────┐
               │PostgreSQL│                      │  LocalStorage  │
               └──────────┘                      │(output images) │
                        │                        └────────────────┘
                        ▼
               ┌──────────────────┐
               │    Scrapers      │
               │  (BeautifulSoup) │
               │ Falabella, Ripley│
               │ Paris, Maui, Zara│
               └──────────────────┘
```

**Flujo principal:**
1. **Scrapers** extraen productos → **Backend** los procesa y almacena en **PostgreSQL**
2. **Usuario** navega en **Frontend** → solicita productos desde **Backend API**
3. **Usuario** sube foto + selecciona producto → **Backend** envía a **VTON Service** → resultado se muestra en **Frontend**
4. **LLM (Gemini 2.0 Flash)** genera recomendaciones personalizadas basadas en preferencias del usuario

## Jerarquía de Clases (POO)

### Scrapers

```
BaseScraper (abstract)
├── FalabellaScraper
├── RipleyScraper
├── ParisScraper
├── MauiScraper
└── ZaraScraper
```

Cada scraper hereda de `BaseScraper` e implementa los métodos abstractos `fetch_products()`, `parse_product()` y `normalize_data()`.

### Orquestador (backend)

```
PipelineOrchestrator
├── ScrapingCoordinator   — coordina la ejecución de todos los scrapers
├── VTONCoordinator       — gestiona el pipeline de Virtual Try-On
└── PublicationManager    — controla la publicación de productos (draft → published)
```

### Servicios (backend)

```
UserService              — registro, autenticación, perfil, medidas
ProductService           — CRUD de productos, búsqueda, filtros
RecommendationService    — recomendaciones vía LLM + embeddings
VTONService              — integración con el modelo de diffusion
```

### Clientes de infraestructura

```
LLMClient    — wrapper sobre LangChain + GPT-4
VTONClient   — comunicación HTTP con el servicio VTON
ScraperClient— comunicación HTTP con el servicio de scrapers
```

### Modelos de dominio

```
User         — usuario con email, password hash, medidas corporales, preferencias
Product      — producto con metadata de tienda, precio, categoría, tallas, colores
VTONResult   — resultado de try-on virtual con estado (pending/processing/completed/failed)
```

## Clean Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (api/v1/routes/)            │
│              FastAPI Routers + Middleware                │
│              auth, users, products,                      │
│              recommendations, vton                       │
├─────────────────────────────────────────────────────────┤
│                Application Layer (application/)          │
│    ┌───────────────────┐  ┌──────────────────────────┐  │
│    │     Services      │  │      Orchestrator        │  │
│    │ UserService, etc. │  │ PipelineOrchestrator,    │  │
│    │                   │  │ ScrapingCoordinator,     │  │
│    │                   │  │ VTONCoordinator,         │  │
│    │                   │  │ PublicationManager       │  │
│    └───────────────────┘  └──────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer (domain/)                 │
│              Models: User, Product, VTONResult           │
├─────────────────────────────────────────────────────────┤
│             Infrastructure Layer (infrastructure/)       │
│    ┌─────────────────────┐  ┌────────────────────────┐  │
│    │  Persistence        │  │  External Services     │  │
│    │  postgres/models.py │  │  LLMClient, VTONClient,│  │
│    │  repositories/      │  │  ScraperClient         │  │
│    └─────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Integración de IA (LLM)

El `LLMClient` es un wrapper sobre Gemini 2.0 Flash para:
- Recomendaciones personalizadas por preferencias
- Validación y limpieza de datos scrapeados
- Generación de descripciones y tags

## Comunicación entre servicios

```
┌──────────────┐      HTTP/JSON       ┌──────────────┐
│   Backend    │◄─────────────────────►│   VTON App   │
│   (FastAPI)  │                       │  (PyTorch)   │
│   :8000      │                       │  :8002       │
└──────┬───────┘                       └──────────────┘
       │
       │  HTTP/JSON
       ▼
┌──────────────┐
│   Scrapers   │
│  (FastAPI)   │
│  :8001       │
└──────────────┘
```

## Seguridad

- **Autenticación**: JWT (access + refresh tokens)
- **Hash de contraseñas**: bcrypt con salt
- **Transporte**: HTTPS / TLS en producción
- **Autorización**: Middleware JWT en cada endpoint protegido
