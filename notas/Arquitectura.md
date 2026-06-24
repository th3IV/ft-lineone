# Arquitectura del Sistema

**FT. THE LINE ONE** — Plataforma B2C de Fashion Tech con 4 microservicios.

## Diagrama General

```
Frontend React (:3000)
    ↕ HTTP/JSON
Backend FastAPI (:8000)
    ↕                    ↕
VTON Service (:8002)   Scrapers Service (:8001)
```

## Microservicios

| Servicio | Tech Stack | Puerto |
|---|---|---|
| **Backend API** | FastAPI + PostgreSQL/SQLite | `:8000` |
| **Frontend Web** | React 19 + TailwindCSS 4 | `:3000` |
| **Scrapers** | Python + BeautifulSoup | `:8001` |
| **VTON** | Diffusion Models + PyTorch | `:8002` |

## Clean Architecture (Backend)

```
API Layer        → routes/ (auth, products, users, recommendations, vton, scrapers)
Application      → services/ + orchestrator/
Domain           → models/ (User, Product, VTONResult)
Infrastructure   → persistence/ (postgres repos) + external_services/ (LLM, VTON)
```

## Flujo Principal

1. **Scrapers** extraen productos → Backend los procesa → PostgreSQL
2. **Usuario** navega en Frontend → consume API de productos
3. **Virtual Try-On**: usuario sube foto + selecciona producto → VTON Service → resultado en LocalStorage
4. **LLM (Gemini 2.0 Flash)** genera recomendaciones personalizadas

## Seguridad

- JWT (access 30min + refresh 7 días)
- bcrypt para passwords
- HTTPS/TLS en producción

## Enlaces

- [[docs/architecture|Documentación oficial de arquitectura]]
- [[docs/api|Documentación de API]]
- [[Scrapers]]
- [[VTON]]
