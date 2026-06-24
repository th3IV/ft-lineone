import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import httpx

from src.core.config import settings


class SupabaseRestClient:
    _client: httpx.Client | None = None
    _base_url: str = ""
    _headers: dict = {}

    @classmethod
    def initialize(cls):
        if cls._client is None:
            url = settings.SUPABASE_URL.rstrip("/")
            key = settings.SUPABASE_SERVICE_ROLE_KEY
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
            cls._base_url = f"{url}/rest/v1"
            cls._headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Prefer": "return=representation",
            }
            cls._client = httpx.Client(base_url=cls._base_url, headers=cls._headers, timeout=30)

    @classmethod
    def get_client(cls) -> httpx.Client:
        if cls._client is None:
            cls.initialize()
        return cls._client


class UserRestRepository:
    def __init__(self):
        self.client = SupabaseRestClient.get_client()
        self.table = "users"

    def _rpc_url(self, func: str) -> str:
        url = settings.SUPABASE_URL.rstrip("/")
        return f"{url}/rest/v1/rpc/{func}"

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        r = self.client.get(f"/{self.table}", params={"email": f"eq.{email}", "limit": "1"})
        if r.status_code == 200 and r.json():
            return r.json()[0]
        return None

    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        r = self.client.get(f"/{self.table}", params={"id": f"eq.{user_id}", "limit": "1"})
        if r.status_code == 200 and r.json():
            return r.json()[0]
        return None

    async def create(self, user: Dict[str, Any]) -> Dict[str, Any]:
        user["id"] = user.get("id") or str(uuid.uuid4())
        user["created_at"] = user.get("created_at") or datetime.now(timezone.utc).isoformat()
        user["updated_at"] = datetime.now(timezone.utc).isoformat()
        r = self.client.post(f"/{self.table}", json=user)
        r.raise_for_status()
        return r.json()[0]


class VTONRestRepository:
    def __init__(self):
        self.client = SupabaseRestClient.get_client()
        self.table = "vton_results"

    async def create_pending(
        self,
        job_id: str,
        user_id: str,
        product_id: str,
        input_image_url: str,
        garment_image_url: str = "",
        hf_job_id: str = "",
    ) -> Dict[str, Any]:
        data = {
            "id": job_id,
            "user_id": user_id,
            "product_id": product_id,
            "input_image_url": input_image_url,
            "garment_image_url": garment_image_url,
            "status": "pending",
            "error": "",
            "hf_job_id": hf_job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        r = self.client.post(f"/{self.table}", json=data)
        r.raise_for_status()
        return r.json()[0]

    async def update_processing(self, job_id: str, hf_job_id: str) -> Optional[Dict[str, Any]]:
        r = self.client.patch(
            f"/{self.table}",
            params={"id": f"eq.{job_id}"},
            json={
                "status": "processing",
                "hf_job_id": hf_job_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        r.raise_for_status()
        return r.json()[0] if r.json() else None

    async def update_completed(self, job_id: str, output_image_url: str) -> Optional[Dict[str, Any]]:
        r = self.client.patch(
            f"/{self.table}",
            params={"id": f"eq.{job_id}"},
            json={
                "status": "completed",
                "output_image_url": output_image_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        r.raise_for_status()
        return r.json()[0] if r.json() else None

    async def update_failed(self, job_id: str, error: str) -> Optional[Dict[str, Any]]:
        r = self.client.patch(
            f"/{self.table}",
            params={"id": f"eq.{job_id}"},
            json={
                "status": "failed",
                "error": error,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        r.raise_for_status()
        return r.json()[0] if r.json() else None

    async def find_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        r = self.client.get(f"/{self.table}", params={"id": f"eq.{job_id}", "limit": "1"})
        if r.status_code == 200 and r.json():
            return r.json()[0]
        return None

    async def find_by_user(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        r = self.client.get(
            f"/{self.table}",
            params={"user_id": f"eq.{user_id}", "order": "created_at.desc", "limit": str(limit)},
        )
        if r.status_code == 200:
            return r.json()
        return []