# SECURITY FIX — M6: Auth en VTON Service

## Archivo: vton/app/api/routes.py

## PROBLEMA:
El endpoint VTON acepta `user_id` como parámetro del formulario sin verificar JWT.
Cualquiera puede ejecutar try-on impersonando a cualquier usuario.

## CAMBIO ANTES:
```python
@router.post("/try-on")
async def try_on(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),      # VULNERABLE — client sends this
    user_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
):
```

## CAMBIO DESPUÉS:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth import verify_token  # Importa tu función de verificación

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify JWT and return user payload."""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.post("/try-on")
async def try_on(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),  # SEGURO — JWT verified
    user_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
):
    user_id = user["sub"]  # Extract from verified JWT, not from client
```

## Frontend — enviar Authorization header:
```javascript
const response = await fetch('/api/v1/vton/try-on', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
    body: formData,
});
```

## Rate limiting en auth (adicional):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")  # 5 intentos por minuto por IP
async def login(request: Request, ...):
    ...

@router.post("/auth/register")
@limiter.limit("3/minute")  # 3 registros por minuto por IP
async def register(request: Request, ...):
    ...
```
