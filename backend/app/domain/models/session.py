from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class Session:
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
