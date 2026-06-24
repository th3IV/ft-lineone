# Frontend — React + TailwindCSS

> Aplicación React 19 en `:3000`. TailwindCSS v4.

## Páginas

| Ruta | Componente | Descripción |
|------|------------|-------------|
| `/` | Home | Landing + login/register |
| `/catalog` | Catalog | Listado de productos |
| `/product/:id` | ProductDetail | Detalle del producto |
| `/virtual-try-on` | VirtualTryOn | Probador virtual |
| `/profile` | Profile | Perfil del usuario |

## Componentes

| Componente | Descripción |
|------------|-------------|
| `Navbar` | Barra de navegación |
| `ProductCard` | Tarjeta de producto |
| `ProductGrid` | Grid de productos |
| `VirtualMirror` | Espejo virtual (VTON) |
| `StyleQuiz` | Quiz de preferencias |

## Servicios (API Client)

| Archivo | Descripción |
|---------|-------------|
| `api.js` | Axios instance + interceptors (JWT, 401 redirect) |
| `auth.js` | Auth helpers (login, register, refresh) |
| `vton.js` | VTON API calls (requestTryOn, getResult, getHistory) |

## API Client

Axios configurado con:
- `baseURL`: `REACT_APP_API_URL || http://localhost:8000/api`
- Interceptor de request: agrega `Authorization: Bearer <token>` desde localStorage
- Interceptor de response: 401 → limpia token → redirige a `/login`

## Enlaces

- [[API Endpoints]]
- [[Arquitectura]]
- [[Setup y Desarrollo]]
