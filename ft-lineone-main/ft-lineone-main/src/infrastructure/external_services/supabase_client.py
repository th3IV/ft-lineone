from typing import Optional
import httpx
from src.core.config import settings


class SupabaseAuthResponse:
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.email = data.get("email", "")


class SupabaseSessionResponse:
    def __init__(self, data: dict):
        self.access_token = data.get("access_token", "")
        self.refresh_token = data.get("refresh_token", "")
        self.expires_in = data.get("expires_in", 0)
        self.token_type = data.get("token_type", "bearer")


class SupabaseUserResponse:
    def __init__(self, data: dict):
        user_data = data.get("user", data)
        self.id = user_data.get("id", "")
        self.email = user_data.get("email", "")
        self.user_metadata = user_data.get("user_metadata", {})


class SupabaseClient:
    _base_url: str = ""
    _anon_key: str = ""
    _service_key: str = ""

    @classmethod
    def _init(cls):
        if not cls._base_url:
            cls._base_url = settings.SUPABASE_URL.rstrip("/")
            cls._anon_key = settings.SUPABASE_KEY
            cls._service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    @classmethod
    def _headers(cls, use_service_role: bool = False) -> dict:
        cls._init()
        key = cls._service_key if use_service_role else cls._anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def sign_up(cls, email: str, password: str, user_data: dict | None = None) -> dict:
        cls._init()
        payload = {
            "email": email,
            "password": password,
            "data": user_data or {},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/signup",
                headers=cls._headers(),
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "user": SupabaseAuthResponse(data),
                "session": SupabaseSessionResponse(data) if "access_token" in data else None,
            }

    @classmethod
    async def sign_in(cls, email: str, password: str) -> dict:
        cls._init()
        payload = {"email": email, "password": password}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/token?grant_type=password",
                headers=cls._headers(),
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "user": SupabaseAuthResponse(data),
                "session": SupabaseSessionResponse(data),
            }

    @classmethod
    async def sign_out(cls, access_token: str) -> dict:
        cls._init()
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {access_token}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/logout",
                headers=headers,
            )
            return {"success": r.status_code < 400}

    @classmethod
    async def get_user(cls, access_token: str) -> SupabaseUserResponse | None:
        cls._init()
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {access_token}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{cls._base_url}/auth/v1/user",
                headers=headers,
            )
            if r.status_code == 200:
                return SupabaseUserResponse(r.json())
            return None

    @classmethod
    async def refresh_session(cls, refresh_token: str) -> dict:
        cls._init()
        payload = {"refresh_token": refresh_token}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/token?grant_type=refresh_token",
                headers=cls._headers(),
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "session": SupabaseSessionResponse(data),
                "user": SupabaseAuthResponse(data),
            }

    @classmethod
    async def update_user(cls, access_token: str, user_data: dict) -> dict:
        cls._init()
        headers = cls._headers()
        headers["Authorization"] = f"Bearer {access_token}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.put(
                f"{cls._base_url}/auth/v1/user",
                headers=headers,
                json=user_data,
            )
            r.raise_for_status()
            return {"user": SupabaseUserResponse(r.json())}

    @classmethod
    async def admin_create_user(cls, email: str, password: str, user_data: dict | None = None) -> dict:
        cls._init()
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "data": user_data or {},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/admin/users",
                headers=cls._headers(use_service_role=True),
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "user": SupabaseAuthResponse(data),
                "session": None,
            }

    @classmethod
    async def reset_password_email(cls, email: str) -> dict:
        cls._init()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{cls._base_url}/auth/v1/recover",
                headers=cls._headers(),
                json={"email": email},
            )
            return {"success": r.status_code < 400}

    @classmethod
    async def update_password(cls, access_token: str, new_password: str) -> dict:
        return await cls.update_user(access_token, {"password": new_password})