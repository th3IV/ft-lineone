---
name: process_product_image
description: Sube imagen a Cloudinary, genera transformaciones, retorna URLs optimizadas
model: deterministic
---

## Logic (No LLM)
1. Descargar imagen desde URL original (httpx, timeout 30s)
2. Validar MIME type (image/jpeg, image/png, image/webp)
3. Subir a Cloudinary: folder="products/{store}/{external_id}/"
4. Generar transformaciones:
   - thumbnail: w_200,h_200,c_fill,q_auto,f_auto
   - card: w_400,h_400,c_fill,q_auto,f_auto
   - detail: w_800,q_auto,f_auto
   - original: q_auto,f_auto
5. Retornar array de ProductImage con secure_urls

## Input Schema
{
  "external_id": "string",
  "store": "zara|hm",
  "image_url": "string",
  "is_primary": true
}

## Output Schema
{
  "images": [
    {"url": "https://res.cloudinary.com/.../thumbnail.jpg", "width": 200, "height": 200, "is_primary": true},
    {"url": "https://res.cloudinary.com/.../card.jpg", "width": 400, "height": 400, "is_primary": false},
    {"url": "https://res.cloudinary.com/.../detail.jpg", "width": 800, "height": 1000, "is_primary": false}
  ]
}