# Documentación de API REST

**Base URL**: `http://localhost:8000/api/v1`

## Autenticación

Todas las rutas protegidas requieren un token JWT en el header:

```
Authorization: Bearer <token>
```

### POST /auth/register

Registro de nuevo usuario.

**Request body:**
```json
{
  "name": "María García",
  "email": "usuario@ejemplo.com",
  "password": "MiPassword123!"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "name": "María García",
    "email": "usuario@ejemplo.com"
  }
}
```

### POST /auth/login

Inicio de sesión.

**Request body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "MiPassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "name": "María García",
    "email": "usuario@ejemplo.com"
  }
}
```

### POST /auth/refresh

Renueva el token de acceso usando el refresh token.

**Request body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Usuarios

### GET /users/me

Obtiene el perfil del usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "email": "usuario@ejemplo.com",
  "name": "María García",
  "body_measurements": {
    "height": 165,
    "weight": 60,
    "bust": 90,
    "waist": 68,
    "hips": 96,
    "shoulder_width": 40
  },
  "preferences": ["vestidos", "blusas"],
  "created_at": "2026-06-10T12:00:00Z"
}
```

### PUT /users/me/measurements

Actualiza las medidas corporales del usuario.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "body_measurements": {
    "height": 165,
    "weight": 60,
    "bust": 90,
    "waist": 68,
    "hips": 96,
    "shoulder_width": 40
  }
}
```

**Response (200):**
```json
{
  "body_measurements": {
    "height": 165,
    "weight": 60,
    "bust": 90,
    "waist": 68,
    "hips": 96,
    "shoulder_width": 40
  }
}
```

### GET /users/me/history

Obtiene el historial de interacciones del usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "user_id": "uuid",
  "history": []
}
```

## Productos

### GET /products

Lista paginada de productos con filtros.

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|---|
| page | int | 1 | Número de página |
| per_page | int | 20 | Productos por página (max 100) |
| store | string | — | Filtrar por tienda (falabella, ripley, etc.) |
| category | string | — | Filtrar por categoría |
| min_price | float | — | Precio mínimo |
| max_price | float | — | Precio máximo |

**Response (200):**
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Vestido Floral Verano",
      "store": "falabella",
      "price": 29990,
      "category": "vestidos",
      "image_url": "https://s3.amazonaws.com/ft-lineone/products/vestido.jpg",
      "description": "Vestido largo estampado floral, manga corta...",
      "sizes": ["XS", "S", "M", "L", "XL"],
      "colors": ["azul", "blanco"],
      "created_at": "2026-06-10T12:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

### GET /products/{id}

Obtiene un producto por su ID.

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Vestido Floral Verano",
  "store": "falabella",
  "price": 29990,
  "category": "vestidos",
  "image_url": "https://s3.amazonaws.com/ft-lineone/products/vestido.jpg",
  "description": "Vestido largo estampado floral, manga corta...",
  "sizes": ["XS", "S", "M", "L", "XL"],
  "colors": ["azul", "blanco"],
  "created_at": "2026-06-10T12:00:00Z"
}
```

### GET /products/search

Búsqueda textual de productos.

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|---|
| q | string | — | Término de búsqueda |
| page | int | 1 | Número de página |
| per_page | int | 20 | Productos por página |

**Response (200):**
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Vestido Floral Verano",
      "store": "falabella",
      "price": 29990
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### GET /products/store/{store}

Lista productos filtrados por tienda.

**Path parameters:**

| Parámetro | Descripción |
|---|---|
| store | Nombre de la tienda (falabella, ripley, paris, maui, zara) |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|---|
| page | int | 1 | Número de página |
| per_page | int | 20 | Productos por página |

**Response (200):**
```json
{
  "store": "falabella",
  "products": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

## Recomendaciones

### GET /recommendations

Obtiene recomendaciones personalizadas basadas en preferencias e historial del usuario.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "user_id": "uuid",
  "recommendations": [
    {
      "id": "uuid",
      "name": "Vestido Floral Verano",
      "store": "falabella",
      "price": 29990,
      "image_url": "https://s3.amazonaws.com/ft-lineone/products/vestido.jpg",
      "category": "vestidos",
      "sizes": ["XS", "S", "M", "L", "XL"],
      "colors": ["azul", "blanco"],
      "created_at": "2026-06-10T12:00:00Z"
    }
  ],
  "count": 1
}
```

## Virtual Try-On (VTON)

### POST /vton/try-on

Procesa una foto del usuario con una prenda seleccionada.

**Headers:** `Authorization: Bearer <token>` | `Content-Type: multipart/form-data`

**Request body (multipart):**

| Campo | Tipo | Descripción |
|---|---|---|
| user_image | file | Foto del usuario (JPEG, PNG, max 10MB) |
| product_id | string | ID del producto a probar |

**Response (200):**
```json
{
  "vton_id": "uuid",
  "status": "processing",
  "input_image_url": "https://s3.amazonaws.com/ft-lineone/vton/user-123-input.jpg"
}
```

### GET /vton/result/{id}

Obtiene el resultado del Virtual Try-On.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "status": "completed",
  "input_image_url": "https://s3.amazonaws.com/ft-lineone/vton/user-123-input.jpg",
  "output_image_url": "https://s3.amazonaws.com/ft-lineone/vton/user-123-output.jpg",
  "created_at": "2026-06-10T12:00:00Z"
}
```

**States de `status`:** `pending`, `processing`, `completed`, `failed`
