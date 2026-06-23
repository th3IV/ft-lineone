from typing import Optional
from src.infrastructure.external_services.supabase_client import SupabaseClient
from src.infrastructure.database.postgres.repositories import UserRepository
from src.core.security import create_access_token, get_password_hash, verify_password


class AuthUseCases:
    def __init__(self):
        self._user_repo = UserRepository()

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        body_measurements: dict | None = None,
        preferences: list[str] | None = None,
    ) -> dict:
        supabase_result = await SupabaseClient.sign_up(email, password, {"name": name})
        supabase_user = supabase_result["user"]
        session = supabase_result["session"]

        user = {
            "id": supabase_user.id,
            "email": email,
            "password_hash": get_password_hash(password),
            "name": name,
            "body_measurements": body_measurements or {},
            "preferences": preferences or [],
            "avatar_url": "",
        }
        created = await self._user_repo.create(user)

        access_token = create_access_token(subject=supabase_user.id)
        return {
            "user": self._to_user_dict(created),
            "access_token": access_token,
            "refresh_token": session.refresh_token if session else None,
        }

    async def login(self, email: str, password: str) -> dict:
        supabase_result = await SupabaseClient.sign_in(email, password)
        supabase_user = supabase_result["user"]
        session = supabase_result["session"]

        user = await self._user_repo.find_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid credentials")

        access_token = create_access_token(subject=supabase_user.id)
        return {
            "user": self._to_user_dict(user),
            "access_token": access_token,
            "refresh_token": session.refresh_token if session else None,
        }

    async def logout(self, access_token: str) -> dict:
        await SupabaseClient.sign_out(access_token)
        return {"success": True}

    async def get_current_user(self, access_token: str) -> dict | None:
        supabase_user = await SupabaseClient.get_user(access_token)
        if not supabase_user:
            return None
        user = await self._user_repo.find_by_id(supabase_user.id)
        return self._to_user_dict(user) if user else None

    async def refresh_tokens(self, refresh_token: str) -> dict:
        supabase_result = await SupabaseClient.refresh_session(refresh_token)
        session = supabase_result["session"]
        user = await self._user_repo.find_by_id(supabase_result["user"].id)
        access_token = create_access_token(subject=user["id"])
        return {
            "user": self._to_user_dict(user),
            "access_token": access_token,
            "refresh_token": session.refresh_token if session else None,
        }

    async def update_profile(
        self,
        access_token: str,
        name: str | None = None,
        body_measurements: dict | None = None,
        preferences: list[str] | None = None,
    ) -> dict:
        supabase_user = await SupabaseClient.get_user(access_token)
        if not supabase_user:
            raise ValueError("Invalid token")

        update_data = {}
        if name:
            update_data["name"] = name
        if body_measurements:
            update_data["body_measurements"] = body_measurements
        if preferences:
            update_data["preferences"] = preferences

        await SupabaseClient.update_user(access_token, {"data": update_data})

        user = await self._user_repo.find_by_id(supabase_user.id)
        if user:
            user.update(update_data)
            await self._user_repo.create(user)

        return self._to_user_dict(user)

    def _to_user_dict(self, user: dict) -> dict:
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "body_measurements": user.get("body_measurements", {}),
            "preferences": user.get("preferences", []),
            "avatar_url": user.get("avatar_url", ""),
            "created_at": user.get("created_at"),
        }