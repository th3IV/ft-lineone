# SECURITY FIX — M4: Path Traversal

## Archivo: backend/app/api/v1/routes/vton.py

## CAMBIO ANTES:
```python
image_url = f"uploads/{user_id}/{user_image.filename}"
```

## CAMBIO DESPUÉS:
```python
import os
import re
import uuid
from fastapi import UploadFile

def sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters from filename."""
    # Remove path separators
    filename = os.path.basename(filename)
    # Remove null bytes
    filename = filename.replace("\x00", "")
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length
    filename = filename[:100]
    return filename

async def save_upload(user_id: str, file: UploadFile, upload_dir: str = "uploads") -> str:
    """Save uploaded file with sanitized name and unique ID."""
    # Sanitize original filename
    safe_name = sanitize_filename(file.filename or "upload")
    # Add UUID to prevent collisions and enumeration
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    # Build safe path (no user-controlled path components)
    user_dir = os.path.join(upload_dir, sanitize_filename(user_id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, unique_name)

    # Write file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path
```

## En el endpoint:
```python
@router.post("/vton")
async def try_on(
    user_id: str = Form(...),
    user_image: UploadFile = File(...),
    # ...
):
    # ANTES (VULNERABLE):
    # image_url = f"uploads/{user_id}/{user_image.filename}"

    # DESPUÉS (SEGURO):
    image_url = await save_upload(user_id, user_image)
```

## Para el frontend (uploads desde el navegador):
Si el frontend envía base64 en lugar de multipart:
```python
import base64
import uuid

def save_base64_image(user_id: str, data_url: str, upload_dir: str = "uploads") -> str:
    """Save base64 image with sanitized path."""
    # Extract base64 data
    if "," in data_url:
        header, b64data = data_url.split(",", 1)
    else:
        b64data = data_url

    # Decode and save
    img_bytes = base64.b64decode(b64data)
    user_dir = os.path.join(upload_dir, re.sub(r'[^a-zA-Z0-9_-]', '_', user_id))
    os.makedirs(user_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(user_dir, filename)

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    return file_path
```
