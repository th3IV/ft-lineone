# Arquitectura del Sistema

## Visión General

FT. THE LINE ONE está compuesto por **4 microservicios** que trabajan de forma orquestada para ofrecer una experiencia de moda inteligente:

| Microservicio | Tecnología | Rol |
|---|---|---|
| **Backend API** | FastAPI (Python) | Orquestación, usuarios, productos, recomendaciones |
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
                   └───┬─────┬──────┘           └────────┬─────────┘
                       │     │                           │
                       ▼     ▼                           ▼
              ┌──────────┐ ┌────┐              ┌────────────────┐
              │PostgreSQL│ │ S3 │              │       S3       │
              └──────────┘ └─┬──┘              │(output images) │
                             │                 └────────────────┘
                             ▼
              ┌──────────────────┐
              │    Scrapers      │
              │  (BeautifulSoup) │
              │ Falabella, Ripley│
              │ Paris, Maui, Zara│
              └──────────────────┘
```

**Flujo principal:**
1. **Scrapers** extraen productos → **Backend** los procesa y almacena en **PostgreSQL** + **S3** (imágenes)
2. **Usuario** navega en **Frontend** → solicita productos desde **Backend API**
3. **Usuario** sube foto + selecciona producto → **Backend** envía a **VTON Service** → resultado se guarda en **S3** → se muestra en **Frontend**
4. **LLM (GPT-4)** genera recomendaciones personalizadas basadas en preferencias del usuario

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

### Orquestador

```
PipelineOrchestrator
├── ScrapingCoordinator   — coordina la ejecución de todos los scrapers
├── VTONCoordinator       — gestiona el pipeline de Virtual Try-On
└── PublicationManager    — controla la publicación de productos (draft → published)
```

### Servicios

```
UserService          — registro, autenticación, perfil, medidas
ProductService       — CRUD de productos, búsqueda, filtros
RecommendationService — recomendaciones vía LLM + embeddings
VTONService          — integración con el modelo de diffusion
```

## Clean Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       API Layer                         │
│              FastAPI Routers + Middleware                │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                     │
│              Services, Use Cases, DTOs                  │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer                          │
│              Entities, Value Objects, Interfaces        │
├─────────────────────────────────────────────────────────┤
│                Infrastructure Layer                     │
│         DB Repositories, S3 Client, LLM Client          │
└─────────────────────────────────────────────────────────┘
```

## Integración de IA (LLM)

```
User Query
    │
    ▼
RecommendationService
    │
    ▼
LLMClient (LangChain + GPT-4)
    │
    ├── Genera recomendaciones textuales
    ├── Valida descripciones de productos
    └── Enriquece metadata de catálogo
```

El `LLMClient` es un wrapper sobre LangChain que se conecta a GPT-4 para:
- Recomendaciones personalizadas por preferencias
- Validación y limpieza de datos scrapeados
- Generación de descripciones y tags

## Infraestructura AWS

```
                    ┌─────────────────────┐
                    │      VPC            │
                    │  10.0.0.0/16        │
                    └────────┬────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌──────────┐      ┌──────────────┐   ┌──────────┐
   │   EKS    │      │     RDS      │   │ElastiCache│
   │(K8s pods)│      │ (PostgreSQL) │   │  (Redis)  │
   └──────────┘      └──────────────┘   └──────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
 ┌──────┐   ┌────────┐
 │  S3  │   │ Lambda │
 │Media │   │(cron)  │
 └──────┘   └────────┘
```

## Seguridad

- **Autenticación**: JWT (access + refresh tokens)
- **Hash de contraseñas**: bcrypt con salt
- **Transporte**: HTTPS / TLS en producción
- **Autorización**: Middleware JWT en cada endpoint protegido
- **Rate limiting**: implementado a nivel API Gateway
- **Variables sensibles**: almacenadas en AWS Secrets Manager
