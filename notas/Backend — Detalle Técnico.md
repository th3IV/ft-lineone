# Backend — Detalle Técnico

> FastAPI en `:8000`. Clean Architecture con capas API → Application → Domain → Infrastructure.

## Estructura

```
backend/app/
├── api/v1/routes/        # FastAPI routers
│   ├── auth.py           # Register, login, refresh
│   ├── users.py          # Perfil, medidas, historial
│   ├── products.py       # CRUD, búsqueda, filtros
│   ├── recommendations.py# Recomendaciones IA
│   ├── vton.py           # Virtual Try-On endpoints
│   └── scrapers.py       # Ingesta de productos
├── core/
│   ├── config.py         # Settings (pydantic-settings)
│   └── security.py       # JWT + bcrypt utils
├── domain/models/
│   ├── user.py           # User (Pydantic)
│   ├── product.py        # Product (Pydantic)
│   └── vton_result.py    # VTONResult + VTONStatus enum
├── application/services/
│   ├── user_service.py
│   ├── product_service.py
│   ├── recommendation_service.py
│   └── vton_service.py
└── infrastructure/
    ├── persistence/postgres/
    │   ├── models.py     # SQLAlchemy models
    │   ├── session.py    # DB session management
    │   └── repositories/ # ProductRepository, UserRepository
    └── external_services/
        ├── llm_client.py   # Gemini 2.0 Flash wrapper
        └── vton_client.py  # HTTP client para VTON service
```

## LLM Client

Usa **Gemini 2.0 Flash** (Google Generative AI) para:
- Recomendaciones personalizadas
- Validación de datos de productos
- Generación de descripciones
- Análisis del pipeline

Fallback silencioso si no hay API key configurada.

## Modelos de Datos (SQLAlchemy)

| Tabla | Columnas clave |
|-------|----------------|
| `users` | id, name, email, password_hash, body_measurements (JSON), preferences (JSON) |
| `products` | id, external_id, store, name, price, currency, category, sizes (JSON), colors (JSON) |
| `vton_results` | id, user_id, product_id, input_image_url, output_image_url, status |

## Seguridad

- `hash_password()` / `verify_password()` con bcrypt
- `create_access_token()` (30min) / `create_refresh_token()` (7d)
- `verify_token()` con type checking (access vs refresh)

## DB Local

Por defecto SQLite (`sqlite+aiosqlite:///./ft_lineone.db`). Opcionalmente PostgreSQL 16.

## Enlaces

- [[API Endpoints]]
- [[Arquitectura]]
- [[Setup y Desarrollo]]
