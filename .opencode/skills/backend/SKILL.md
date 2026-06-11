---
name: backend
description: >
  Use when working on the FastAPI backend: adding routes, services, models,
  repositories, or dependencies. Covers setup, conventions, and project structure.
---

# Backend Skill

API REST con FastAPI + PostgreSQL, autenticación JWT, servicios de productos, usuarios, recomendaciones y VTON.

## Estructura
```
backend/
├── app/
│   ├── api/v1/routes/          # FastAPI routers
│   ├── core/                   # Config, security
│   ├── domain/models/          # Pydantic domain models
│   ├── application/
│   │   ├── services/           # Business logic services
│   │   └── orchestrator/       # Pipeline orchestration
│   ├── infrastructure/
│   │   ├── persistence/postgres/  # SQLAlchemy models + repos
│   │   └── external_services/     # LLM, VTON, Scraper clients
│   └── main.py
├── tests/
├── requirements.txt
└── Dockerfile
```

## Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Convenciones

### Nuevo endpoint
1. Crear archivo en `api/v1/routes/` con `APIRouter(prefix=...)`
2. Agregar import y `app.include_router(...)` en `main.py`
3. Usar Pydantic `BaseModel` para request/response
4. Inyectar dependencias con `Depends(get_current_user)` para rutas protegidas
5. Importar `Header` desde `fastapi` para el token JWT

### Nuevo modelo de dominio
1. Crear archivo en `domain/models/` heredando de `pydantic.BaseModel`
2. Si tiene persistencia, crear modelo SQLAlchemy en `persistence/postgres/models.py`
3. Crear repositorio en `persistence/postgres/repositories/`

### Nuevo servicio
1. Crear archivo en `application/services/`
2. Inyectar repositorios y clientes en `__init__` con defaults
3. Métodos asíncronos con tipado completo

### Dependencias
- Agregar a `requirements.txt` con versión pinneada
- Preferir `httpx` sobre `requests` para código asíncrono
