# SECURITY FIX — M3: JWT_SECRET seguro

## Archivo: backend/app/core/config.py

## CAMBIO ANTES:
```python
JWT_SECRET: str = "change-me-in-production"
```

## CAMBIO DESPUÉS:
```python
import secrets

JWT_SECRET: str = ""  # Loaded from .env — NEVER default to a hardcoded value
```

## En .env (agregar):
```bash
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET=<generar-secret-fuerte>
```

## Validación en config.py:
```python
from pydantic import field_validator

class Settings(BaseSettings):
    JWT_SECRET: str = ""

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v or v == "change-me-in-production":
            raise ValueError(
                "JWT_SECRET must be set to a secure random string. "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v
```

## Generar secret seguro:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
