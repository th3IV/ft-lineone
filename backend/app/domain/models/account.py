from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class Account:
    id: UUID
    user_id: UUID
    account_type: str  # e.g., 'free', 'premium'
    status: str        # e.g., 'active', 'suspended'
    created_at: datetime
    updated_at: datetime
