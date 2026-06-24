---
name: virtual_try_on
description: Orquesta Virtual Try-On vía Genlook API (primario), con fallback a Grok Imagine y HF Space
model: deterministic
---

## Logic (No LLM - HTTP Client)

1. Recibir: user_image_url, product_image_url, product_id, user_id
2. Subir imágenes a Cloudinary (si no están ya) → obtener URLs públicas
3. **Genlook API (primario)**:
   - POST /try-on con { products: [{externalId, title, images}], person: {image: {source: {url}}} }
   - Poll GET /generations/:id cada 2s hasta COMPLETED/FAILED
   - Retorna resultImageUrl directamente
4. **Si Genlook falla → Grok Imagine** (fallback, no es VTON real)
5. **Si Grok falla → HF Space** (último fallback, lento)
6. Retornar: job_id, status, result_url, error

## Input Schema
{
  "user_id": "string",
  "user_image_url": "string",
  "product_id": "string",
  "product_image_url": "string"
}

## Output Schema
{
  "job_id": "string",
  "status": "completed|failed",
  "result_url": "string|null",
  "error": "string|null"
}

## Genlook API
- POST https://api.genlook.app/tryon/v1/try-on
- GET https://api.genlook.app/tryon/v1/generations/:id
- Auth: x-api-key header
- ~1 crédito por generación (~$0.06/gen)