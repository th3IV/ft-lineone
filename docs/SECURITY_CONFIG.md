# Cloudflare WAF Rate Limiting Rules Configuration

## Reglas de Rate Limiting WAF (Configurar en Cloudflare Dashboard)

### 1. Endpoint `/api/v1/auth/login`
- **Acción**: Block
- **Regla**: `http.request.uri.path eq "/api/v1/auth/login" and http.request.method eq "POST"`
- **Límite**: 10 requests / 10 min / IP
- **Acción al exceder**: Block 15 min

### 2. Endpoint `/api/v1/auth/register`
- **Acción**: Block
- **Regla**: `http.request.uri.path eq "/api/v1/auth/register" and http.request.method eq "POST"`
- **Límite**: 5 requests / hora / IP
- **Acción al exceder**: Block 1 hora

### 3. Endpoint `/api/v1/vton/start`
- **Acción**: Block
- **Regla**: `http.request.uri.path eq "/api/v1/vton/start" and http.request.method eq "POST"`
- **Límite**: 20 requests / 10 min / IP (Free), 100 requests / 10 min / IP (Premium via header)
- **Acción al exceder**: Block 10 min

### 4. Endpoint `/api/v1/recommendations/chat`
- **Acción**: Block
- **Regla**: `http.request.uri.path eq "/api/v1/recommendations/chat" and http.request.method eq "POST"`
- **Límite**: 30 requests / 10 min / IP (Free), 100 requests / 10 min / IP (Premium)
- **Acción al exceder**: Block 10 min

### 5. API General `/api/v1/*`
- **Acción**: Challenge
- **Regla**: `http.request.uri.path matches "^/api/v1/" and not cf.client.bot`
- **Límite**: 100 requests / min / IP
- **Acción al exceder**: Managed Challenge

### 6. Bloqueo de User-Agents maliciosos
- **Regla**: `http.request.headers["user-agent"] contains "sqlmap" or http.request.headers["user-agent"] contains "nikto" or http.request.headers["user-agent"] contains "nmap" or http.request.headers["user-agent"] contains "dirb" or http.request.headers["user-agent"] contains "gobuster"`
- **Acción**: Block

---

## Headers de Seguridad (Configurar en Cloudflare Workers)

```javascript
// En entry.py - headers de seguridad ya implementados en DynamicCORSMiddleware
// Headers adicionales recomendados para Cloudflare:

// Content Security Policy
"Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.thelineone.com https://yce-api-01.makeupar.com wss://api.thelineone.com; frame-ancestors 'none';"

// HSTS
"Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"

// X-Frame-Options
"X-Frame-Options": "DENY"

// X-Content-Type-Options
"X-Content-Type-Options": "nosniff"

// Referrer Policy
"Referrer-Policy": "strict-origin-when-cross-origin"

// Permissions Policy
"Permissions-Policy": "camera=(), microphone=(), geolocation=()"
```

---

## Configuración de Turnstile

### Configuración en Cloudflare Dashboard:
1. Ir a **Turnstile** → **Add Site**
2. **Site name**: ft-lineone
3. **Domain**: thelineone.com, www.thelineone.com, localhost
4. **Widget mode**: Managed (invisible)
5. **Pre-clearance**: On
6. **Copy Site Key y Secret Key**

### Variables de entorno (Wrangler Secrets):
```bash
wrangler secret put TURNSTILE_SITE_KEY
wrangler secret put TURNSTILE_SECRET_KEY
```

### Variables de entorno (wrangler.jsonc vars):
```json
{
  "TURNSTILE_SITE_KEY": "0x4AAAAAAA...",
  "TURNSTILE_SECRET_KEY": "0x4AAAAAAA..."
}
```

---

## Configuración de JWT EdDSA (Ed25519)

### Generar claves:
```bash
# Generar par de claves Ed25519
python3 -c "
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

print('JWT_PRIVATE_KEY=' + base64.b64encode(private_pem).decode())
print('JWT_PUBLIC_KEY=' + base64.b64encode(public_pem).decode())
"
```

### Configurar en Wrangler:
```bash
wrangler secret put JWT_PRIVATE_KEY
wrangler secret put JWT_PUBLIC_KEY
```

---

## Configuración de Argon2id (si se usa)

Si se decide migrar de PBKDF2 a Argon2id (requiere `argon2-cffi`):

```python
# En auth.py - hash_password
import argon2
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID
)
hash = ph.hash(password)

# verify_password
try:
    ph.verify(hash, password)
    return True
except argon2.exceptions.VerifyMismatchError:
    return False
```

---

## Checklist de Seguridad Pre-Deploy

- [ ] Turnstile configurado en login, register, VTON start, chat
- [ ] WAF Rate Limiting rules activadas en Cloudflare Dashboard
- [ ] JWT EdDSA keys generadas y configuradas en Wrangler secrets
- [ ] Argon2id configurado (opcional, requiere argon2-cffi)
- [ ] Headers CSP, HSTS, X-Frame-Options configurados
- [ ] WAF rules para bloquear User-Agents maliciosos
- [ ] Rate limiting WAF en endpoints críticos
- [ ] CORS restrictivo (solo dominios permitidos)
- [ ] Error sanitization en producción (safe_error_message)
- [ ] Webhook secrets configurados (YouCam, Transbank)
- [ ] Logs de auditoría para acciones sensibles (login, payment, admin)