import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserBase(BaseModel):
    email: str
    name: str = Field(..., min_length=1, max_length=100)

    @validator("email")
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    gender: Optional[str] = None
    age: Optional[int] = None


class UserLogin(BaseModel):
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class UserResponse(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    body_measurements: Optional[dict] = None
    preferences: dict = {}
    profile_image: Optional[str] = None
    is_premium: bool = False
    plan_type: str = "free"
    daily_usage: Optional[dict] = None

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    name: Optional[str] = None
    body_measurements: Optional[dict] = None
    preferences: Optional[dict] = None
    profile_image: Optional[str] = None
