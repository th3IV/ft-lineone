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
  "email": "usuario@ejemplo.com",
  "password": "MiPassword123!",
  "name": "María García",
  "phone": "+56912345678"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "usuario@ejemplo.com",
  "name": "María García",
  "created_at": "2026-06-10T12:00:00Z"
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
  "token_type": "bearer",
  "expires_in": 3600
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
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
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
  "phone": "+56912345678",
  "measurements": {
    "height": 165,
    "weight": 60,
    "bust": 90,
    "waist": 68,
    "hips": 96,
    "shoulder_width": 40
  },
  "preferences": {
    "categories": ["vestidos", "blusas"],
    "stores": ["falabella", "ripley"],
    "sizes": ["M"]
  },
  "created_at": "2026-06-10T12:00:00Z"
}
```

### PUT /users/me/measurements

Actualiza las medidas corporales del usuario.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "height": 165,
  "weight": 60,
  "bust": 90,
  "waist": 68,
  "hips": 96,
  "shoulder_width": 40
}
```

**Response (200):**
```json
{
  "message": "Medidas actualizadas correctamente",
  "measurements": {
    "height": 165,
    "weight": 60,
    "bust": 90,
    "waist": 68,
    "hips": 96,
    "shoulder_width": 40
  }
}
```

## Productos

### GET /products

Lista paginada de productos con filtros.

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| page | int | 1 | Número de página |
| limit | int | 20 | Productos por página (max 100) |
| store | string | — | Filtrar por tienda (falabella, ripley, etc.) |
| category | string | — | Filtrar por categoría |
| min_price | float | — | Precio mínimo |
| max_price | float | — | Precio máximo |

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Vestido Floral Verano",
      "brand": "Maui",
      "store": "falabella",
      "price": 29990,
      "original_price": 49990,
      "discount": 40,
      "category": "vestidos",
      "image_url": "https://s3.amazonaws.com/ft-lineone/products/vestido.jpg",
      "product_url": "https://falabella.cl/producto/123",
      "description": "Vestido largo estampado floral, manga corta...",
      "sizes": ["XS", "S", "M", "L", "XL"],
      "colors": ["azul", "blanco"],
      "in_stock": true,
      "created_at": "2026-06-10T12:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

### GET /products/{id}

Obtiene un producto por su ID.

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Vestido Floral Verano",
  "brand": "Maui",
  "store": "falabella",
  "price": 29990,
  "original_price": 49990,
  "discount": 40,
  "category": "vestidos",
  "images": [
    "https://s3.amazonaws.com/ft-lineone/products/vestido-1.jpg",
    "https://s3.amazonaws.com/ft-lineone/products/vestido-2.jpg"
  ],
  "description": "Vestido largo estampado floral, manga corta...",
  "sizes": ["XS", "S", "M", "L", "XL"],
  "colors": ["azul", "blanco"],
  "materials": ["100% poliéster"],
  "care_instructions": ["Lavar a máquina max 30°", "No usar blanqueador"],
  "in_stock": true,
  "created_at": "2026-06-10T12:00:00Z"
}
```

### GET /products/search

Búsqueda textual de productos.

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| q | string | — | Término de búsqueda |
| page | int | 1 | Número de página |
| limit | int | 20 | Productos por página |

**Response (200):**
```json
{
  "query": "vestido floral",
  "items": [
    {
      "id": "uuid",
      "name": "Vestido Floral Verano",
      "store": "falabella",
      "price": 29990
    }
  ],
  "total": 15,
  "page": 1
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
|---|---|---|---|
| page | int | 1 | Número de página |
| limit | int | 20 | Productos por página |

**Response (200):** Misma estructura que `GET /products`.

## Recomendaciones

### GET /recommendations

Obtiene recomendaciones personalizadas basadas en preferencias e historial del usuario.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "recommendations": [
    {
      "product": {
        "id": "uuid",
        "name": "Vestido Floral Verano",
        "store": "falabella",
        "price": 29990,
        "image_url": "https://s3.amazonaws.com/ft-lineone/products/vestido.jpg"
      },
      "reason": "Este vestido floral combina perfectamente con tu estilo veraniego. La silueta en A favorece tu tipo de cuerpo."
    }
  ],
  "generated_at": "2026-06-10T12:00:00Z",
  "model": "gpt-4"
}
```

## Virtual Try-On (VTON)

### POST /vton/try-on

Procesa una foto del usuario con una prenda seleccionada.

**Headers:** `Authorization: Bearer <token>` | `Content-Type: multipart/form-data`

**Request body (multipart):**

| Campo | Tipo | Descripción |
|---|---|---|
| image | file | Foto del usuario (JPEG, PNG, max 10MB) |
| product_id | string | ID del producto a probar |

**Response (200):**
```json
{
  "result_id": "uuid",
  "status": "processing",
  "estimated_time": 15,
  "message": "Tu prueba virtual está siendo procesada"
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
  "original_image_url": "https://s3.amazonaws.com/ft-lineone/vton/user-123-input.jpg",
  "result_image_url": "https://s3.amazonaws.com/ft-lineone/vton/user-123-output.jpg",
  "product": {
    "id": "uuid",
    "name": "Vestido Floral Verano",
    "store": "falabella"
  },
  "created_at": "2026-06-10T12:00:00Z",
  "processing_time": 12.5
}
```

**States de `status`:** `pending`, `processing`, `completed`, `failed`
