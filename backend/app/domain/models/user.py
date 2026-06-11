from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str | None = None
    name: str
    email: str
    password_hash: str
    body_measurements: dict = {}
    preferences: list[str] = []
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
