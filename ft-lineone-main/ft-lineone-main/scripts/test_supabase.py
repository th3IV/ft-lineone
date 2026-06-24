#!/usr/bin/env python3
"""
Test completo Supabase: CRUD via REST API.
Uso: python scripts/test_supabase.py
"""
import asyncio
import uuid
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
ANON_KEY = os.getenv("SUPABASE_KEY", "")

import httpx


async def test_crud():
    from src.infrastructure.external_services.supabase_client import SupabaseClient

    rest = httpx.AsyncClient(
        base_url=f"{SUPABASE_URL}/rest/v1",
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
        },
        timeout=30,
    )

    print("[TEST] Verificando conexion a Supabase REST...")
    r = await rest.get("/")
    assert r.status_code == 200
    print("[TEST] API conectada")

    print("[TEST] Verificando tablas...")
    r1 = await rest.get("/users", params={"select": "id", "limit": "1"})
    r2 = await rest.get("/vton_results", params={"select": "id", "limit": "1"})
    assert r1.status_code == 200, f"Tabla users no existe: {r1.status_code}"
    assert r2.status_code == 200, f"Tabla vton_results no existe: {r2.status_code}"
    print("[TEST] Tablas existentes")

    # Crear usuario via Auth Admin API para cumplir FK auth.users
    print("[TEST] Creando usuario en Auth...")
    test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    auth_result = await SupabaseClient.admin_create_user(test_email, "Test1234!", {"name": "Test User"})
    auth_user = auth_result["user"]
    user_id = auth_user.id
    email = auth_user.email or test_email
    print(f"[TEST] Usuario Auth creado: {user_id} - {email}")

    # Insertar en public.users
    print("[TEST] Insertando en public.users...")
    test_user = {
        "id": user_id,
        "email": email,
        "password_hash": "test_placeholder",
        "name": "Test User",
        "body_measurements": {"height": 175, "weight": 70, "size_top": "M", "size_bottom": "40"},
        "preferences": ["casual", "minimalist"],
    }
    created = await rest.post("/users", json=test_user)
    assert created.status_code == 201, f"Error insert user: {created.status_code} {created.text}"
    print("[TEST] Usuario insertado en public.users")

    # Buscar por email
    print("[TEST] Buscar por email...")
    found = await rest.get("/users", params={"email": f"eq.{email}", "limit": "1"})
    assert found.status_code == 200 and found.json(), "No encontrado por email"
    print(f"[TEST] Encontrado: {found.json()[0]['name']}")

    # Buscar por ID
    print("[TEST] Buscar por ID...")
    by_id = await rest.get("/users", params={"id": f"eq.{user_id}", "limit": "1"})
    assert by_id.status_code == 200 and by_id.json(), "No encontrado por ID"
    print(f"[TEST] Encontrado: {by_id.json()[0]['name']}")

    # Crear VTON result
    print("[TEST] Crear VTON result...")
    vton_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "product_id": str(uuid.uuid4()),
        "input_image_url": "https://cloudinary.com/user.jpg",
        "garment_image_url": "https://cloudinary.com/garment.jpg",
        "status": "pending",
        "hf_job_id": "hf-test-123",
    }
    vton = await rest.post("/vton_results", json=vton_data)
    assert vton.status_code == 201, f"Error creando VTON: {vton.status_code} {vton.text}"
    vton_id = vton.json()[0]["id"]
    print(f"[TEST] VTON creado: {vton_id} - status: pending")

    # Actualizar a completed
    print("[TEST] Completar VTON...")
    updated = await rest.patch(
        "/vton_results",
        params={"id": f"eq.{vton_id}"},
        json={"status": "completed", "output_image_url": "https://cloudinary.com/result.jpg"},
    )
    assert updated.status_code == 200, f"Error actualizando VTON: {updated.status_code}"
    print("[TEST] VTON completado")

    # Historial usuario
    print("[TEST] Historial VTON usuario...")
    history = await rest.get("/vton_results", params={"user_id": f"eq.{user_id}", "order": "created_at.desc"})
    assert history.status_code == 200
    print(f"[TEST] VTONs encontrados: {len(history.json())}")

    # Limpiar
    print("[TEST] Limpiando datos de prueba...")
    await rest.delete("/vton_results", params={"id": f"eq.{vton_id}"})
    await rest.delete("/users", params={"id": f"eq.{user_id}"})
    print("[TEST] Datos de prueba eliminados")

    await rest.aclose()
    print("[TEST] Todos los tests pasaron!")


if __name__ == "__main__":
    asyncio.run(test_crud())