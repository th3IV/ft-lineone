# API Endpoints — `/api/v1`

> Backend FastAPI en `:8000`. Auth con JWT via `Authorization: Bearer <token>`.

## Autenticación

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Registro (name, email, password) |
| POST | `/auth/login` | No | Login (email, password) |
| POST | `/auth/refresh` | No | Renovar tokens |

## Usuarios

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/users/me` | Sí | Perfil completo + medidas |
| PUT | `/users/me/measurements` | Sí | Actualizar medidas corporales |
| GET | `/users/me/history` | Sí | Historial de interacciones |

## Productos

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/products` | No | Lista paginada (page, per_page) |
| GET | `/products/search?q=` | No | Búsqueda textual |
| GET | `/products/store/{store}` | No | Filtrar por tienda |
| GET | `/products/{id}` | No | Detalle del producto |

## Recomendaciones

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/recommendations` | Sí | Recomendaciones IA (limit) |

## Virtual Try-On

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/vton/try-on` | Sí | Procesar foto + prenda (multipart) |
| GET | `/vton/result/{id}` | Sí | Obtener resultado VTON |

## Scrapers (ingesta)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/scrapers/ingest` | No | Ingestar producto desde scraper |

## Health

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check del backend |

## Enlaces

- [[docs/api|Documentación oficial con ejemplos JSON]]
- [[Arquitectura]]
- [[Scrapers]]
