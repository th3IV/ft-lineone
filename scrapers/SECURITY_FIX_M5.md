# SECURITY FIX — M5: CORS Restrictido

## Archivo: backend/app/main.py

## CAMBIO ANTES:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # VULNERABLE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## CAMBIO DESPUÉS:
```python
import os

# Allowed origins (configure per environment)
ALLOWED_ORIGINS = [
    "http://localhost:3000",           # Dev frontend
    "http://localhost:5173",           # Vite dev
    "https://ft-lineone.pages.dev",    # Production frontend
    "https://feat-cloudflare-migration.ft-lineone.pages.dev",  # Staging
]

# Production override from env
if os.getenv("CORS_ORIGINS"):
    ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # RESTRICTED
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-Id"],
    max_age=600,  # Cache preflight for 10 min
)
```

## En .env:
```bash
CORS_ORIGINS=https://ft-lineone.pages.dev,https://feat-cloudflare-migration.ft-lineone.pages.dev
```
