# Arquitectura del Sistema — FT. THE LINE ONE

## Visión General

FT. THE LINE ONE opera sobre una arquitectura **Serverless Edge en Cloudflare**, combinando computación distribuida global, bases de datos serverless (D1 y Vectorize), almacenamiento de objetos ($0 egress con R2) e inteligencia artificial generativa con Virtual Try-On (VTON).

| Capa | Tecnología | Rol |
|---|---|---|
| **Frontend Web** | Astro 7 + React 19 + Tailwind 4 | Interfaz B2C optimizada (Islands Architecture) en Cloudflare Pages |
| **Backend API** | Cloudflare Workers Python + FastAPI | API edge global, auth JWT, RAG, endpoints de scrapers y VTON |
| **Database** | Cloudflare D1 (SQLite serverless) | Catálogo de productos, usuarios, historial VTON, tracking de scrapers |
| **Vector DB / RAG** | Cloudflare Vectorize + BGE-M3 | Búsqueda semántica y recomendaciones de estilo contextuales |
| **Colas de Tareas** | Cloudflare Queues + DLQ | Procesamiento desacoplado y resiliente de scrapers de retailers |
| **Storage** | Cloudflare R2 | Almacenamiento persistente de imágenes de perfil, VTON y catálogo |
| **AI / LLM** | Cloudflare Workers AI + Moondream | Llama 4 Scout, DeepSeek R1 y Moondream visión |
| **VTON** | YouCam AI Clothes V3.0 | API externa especializada en Virtual Try-On de alta fidelidad |
| **Pagos** | Transbank WebPay Plus REST | Procesamiento de suscripciones y pagos en CLP |
| **Scheduler** | Cloudflare Native Cron Triggers | Disparo automático de colas de scraping y polling de tareas VTON |

---

## Diagrama de Flujo de Datos

```
                         ┌──────────────────────────────────────────┐
                         │      Frontend Web (Astro 7 / React 19)   │
                         │             Cloudflare Pages             │
                         └──┬───────────────────────────────┬───────┘
                            │ HTTP / JSON                  │
                            ▼                              │
                 ┌───────────────────────┐                 │
                 │   Backend API (Edge)  │                 │
                 │ Workers Python+FastAPI│                 │
                 └───┬───┬──────┬────┬───┘                 │
                     │   │      │    │                     │
         ┌───────────┘   │      │    └────────────┐        │
         ▼               ▼      ▼                 ▼        ▼
   ┌───────────┐   ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────┐
   │Cloudflare │   │Cloudfl. │ │Cloudflare│ │WorkersAI│ │YouCam│
   │    D1     │   │ Queues  │ │    R2    │ │ Llama 4 │ │ VTON │
   │ (SQLite)  │   │(Scraper)│ │ ($0 eg.) │ │Moondream│ │ API  │
   └───────────┘   └────┬────┘ └──────────┘ └─────────┘ └──────┘
                        │
                        ▼ (Queue Consumer)
               ┌──────────────────┐
               │ Scraper Runner   │
               │ (httpx async):   │
               │ - Zara           │
               │ - Maui & Sons    │
               │ - Falabella      │
               │ - H&M            │
               │ - Fashion Park   │
               └────────┬─────────┘
                        │
                        ▼ (Upsert + Index)
               ┌──────────────────┐
               │    Vectorize     │
               │ (BGE-M3 RAG Cat) │
               └──────────────────┘
```

---

## Componentes Clave

### 1. Scraper Pipeline & Resiliencia
- **Disparo:** Cloudflare Native Cron Triggers (`triggers.crons` en `wrangler.jsonc`) o manual vía `/api/v1/scrapers/run`.
- **Desacoplamiento:** El trigger encola jobs por tienda en `SCRAPER_QUEUE` con backoff exponencial.
- **Dead-Letter Queue:** Mensajes que fallan 3 reintentos se desvían a `scraper-jobs-dlq`.
- **Zero-Downtime:** Ingesta vía UPSERT `ON CONFLICT(external_id, store)` en D1 actualizando `last_seen`.
- **Sincronización RAG:** Eliminación de productos obsoletos (`>48h`) desindexa automáticamente de Cloudflare Vectorize.

### 2. Flujo Virtual Try-On (VTON)
1. Usuario sube foto en el frontend (validación de magic bytes y tamaño <8MB).
2. Backend valida la imagen, la sube a `freeimage.host` (URL pública accesible para YouCam) y obtiene la imagen de la prenda desde el catálogo.
3. Se crea tarea en YouCam API y se registra en D1 como `status: "processing"`.
4. El Cron Trigger (`*/2 * * * *`) ejecuta `process_pending_vton_tasks` para pollear tareas pendientes.
5. Al completarse, el resultado se descarga y almacena permanentemente en Cloudflare R2 (`save_vton_output_to_r2`).
6. Se actualiza el resultado en D1 con la URL pública de R2.

### 3. Seguridad
- **Autenticación:** JWT con firma HMAC-SHA256, expiración corta para access tokens y rotación de refresh tokens.
- **Revocación:** Tabla `revoked_tokens` en D1 para invalidación inmediata de tokens en logout.
- **Rate Limiting:** Control de intentos por IP y credenciales con `login_attempts` en D1.
- **Validación de Archivos:** Magic bytes en imágenes de avatar y VTON para prevenir archivos maliciosos.
