from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import hash_password, verify_password
from app.domain.models.user import User
from app.infrastructure.persistence.postgres.repositories.user_repository import (
    UserRepository,
)


class UserService:
    def __init__(self, user_repo: UserRepository | None = None):
        self._user_repo = user_repo or UserRepository()

    async def register(self, name: str, email: str, password: str) -> User:
        existing = await self._user_repo.find_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        user = User(
            id=str(uuid4()),
            name=name,
            email=email,
            password_hash=hash_password(password),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return await self._user_repo.create(user)

    async def login(self, email: str, password: str) -> User:
        user = await self._user_repo.find_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        return user

    async def get_profile(self, user_id: str) -> User:
        user = await self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    async def update_measurements(self, user_id: str, measurements: dict) -> User:
        user = await self._user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.body_measurements = measurements
        user.updated_at = datetime.now(timezone.utc)
        return await self._user_repo.update(user)
