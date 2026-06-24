#!/usr/bin/env python3
"""
Ejecuta migraciones SQL en Supabase via REST API (PostgREST).
Uso: python scripts/setup_supabase.py
Requiere: .env con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY configurados
"""
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("[MIGRATE] ERROR: Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env primero")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

REST_URL = f"{SUPABASE_URL}/rest/v1"


def run_migrations():
    client = httpx.Client(base_url=REST_URL, headers=HEADERS, timeout=30)

    print("[MIGRATE] Verificando conexion a Supabase...")

    r = client.get("/")
    if r.status_code != 200:
        print(f"[MIGRATE] ERROR conectando: {r.status_code} {r.text[:200]}")
        return

    print("[MIGRATE] API conectada")

    print("[MIGRATE] Verificando tablas existentes...")
    try:
        r_users = client.get("/users", params={"select": "id", "limit": "1"})
        r_vton = client.get("/vton_results", params={"select": "id", "limit": "1"})
        if r_users.status_code == 200:
            print("[MIGRATE] Tabla 'users' existe")
        if r_vton.status_code == 200:
            print("[MIGRATE] Tabla 'vton_results' existe")
        if r_users.status_code == 200 and r_vton.status_code == 200:
            print("[MIGRATE] Migraciones ya aplicadas")
            return
    except Exception:
        pass

    print("[MIGRATE] Las tablas no existen - debes crearlas manualmente en Supabase Dashboard.")
    print()
    print("=" * 60)
    print("SQL: Abre Supabase Dashboard -> SQL Editor -> Nueva consulta")
    print("     Pega y ejecuta el siguiente SQL:")
    print("=" * 60)
    print()
    MIGRATION_SQL = """-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla users (sync con auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    body_measurements JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '[]',
    avatar_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla vton_results
DO $$ BEGIN
    CREATE TYPE vton_status AS ENUM ('pending', 'processing', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS public.vton_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    input_image_url TEXT NOT NULL,
    garment_image_url TEXT NOT NULL,
    output_image_url TEXT DEFAULT '',
    status vton_status DEFAULT 'pending',
    error TEXT DEFAULT '',
    hf_job_id TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_vton_user_id ON public.vton_results(user_id);
CREATE INDEX IF NOT EXISTS idx_vton_status ON public.vton_results(status);
CREATE INDEX IF NOT EXISTS idx_vton_product_id ON public.vton_results(product_id);

-- RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vton_results ENABLE ROW LEVEL SECURITY;

-- Politicas users
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Politicas vton_results
DROP POLICY IF EXISTS "Users can view own VTONs" ON public.vton_results;
CREATE POLICY "Users can view own VTONs" ON public.vton_results
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own VTONs" ON public.vton_results;
CREATE POLICY "Users can insert own VTONs" ON public.vton_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own VTONs" ON public.vton_results;
CREATE POLICY "Users can update own VTONs" ON public.vton_results
    FOR UPDATE USING (auth.uid() = user_id);

-- Trigger updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END; $$;

DROP TRIGGER IF EXISTS trigger_users_updated_at ON public.users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS trigger_vton_updated_at ON public.vton_results;
CREATE TRIGGER trigger_vton_updated_at
    BEFORE UPDATE ON public.vton_results
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();"""
    print(MIGRATION_SQL)
    print()
    print("=" * 60)
    print("[MIGRATE] Luego ejecuta: python scripts/test_supabase.py")


if __name__ == "__main__":
    run_migrations()