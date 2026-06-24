---
name: scraper_pipeline
description: Orquesta pipeline completo: validate → normalize → process_image → save to MongoDB
---

## Pipeline Steps
1. **validate_product_data** (Gemini) → filtrar inválidos
2. **normalize_product** (Gemini) → schema canónico MongoDB
3. **process_product_image** (Cloudinary) → URLs optimizadas
4. **MongoProductRepository.save()** → upsert por external_id+store

## Input
{
  "store": "zara|hm",
  "raw_products": [{"external_id": "...", "store": "...", ...}, ...]
}

## Output
{
  "saved": 12,
  "rejected": 3,
  "errors": ["reason1", "reason2"],
  "products": ["external_id1", "external_id2", ...]
}