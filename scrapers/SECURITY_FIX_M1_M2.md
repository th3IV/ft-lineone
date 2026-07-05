# SECURITY FIX — M1-M2: Credenciales comprometidas

## Acción REQUERIDA (no automatizable)

### 1. MongoDB Atlas
1. Ir a https://cloud.mongodb.com → Project → Database Access
2. Eliminar usuario `felipeignaciomorasoto_db_user`
3. Crear nuevo usuario con password fuerte
4. Actualizar `MONGODB_URI` en `.env` del backend
5. Actualizar `MONGODB_URI` en `.env` de la carpeta scrapers

### 2. Supabase PostgreSQL
1. Ir a https://supabase.com → Project → Settings → Database
2. Cambiar password del superuser `postgres`
3. Actualizar `cone.MD` con la nueva URL
4. Actualizar todas las apps que usen esta conexión

### 3. Limpiar historial de git
```bash
# Instalar BFG Repo-Cleaner (https://rtyley.github.io/bfg-repo-cleaner/)
# Clonar repo bare
git clone --mirror https://github.com/th3IV/ft-lineone.git

# Ejecutar BFG para eliminar archivos comprometidos
bfg --delete-files atlas-credentials.env
bfg --delete-files cone.MD
bfg --replace-text passwords.txt

# Push limpio
cd ft-lineone.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push
```

### 4. Forzar rotación de tokens
- GitHub: Settings → Developer Settings → Personal access tokens → Regenerar
- Supabase: Settings → API → Regenerar anon/service_role keys
- MongoDB: Database Access → Reset password

### 5. Verificar
```bash
# Escanear historial por credenciales
git log --all --full-history -- "*.env" "*.MD" | grep -i "password\|secret\|token\|credential"
```
