from typing import Optional, List, Dict, Any
from src.infrastructure.database.postgres.supabase_rest_client import UserRestRepository, VTONRestRepository


UserRepository = UserRestRepository
VTONRepository = VTONRestRepository


async def init_db():
    """No-op: tables are created via SQL Editor in Supabase Dashboard."""
    pass