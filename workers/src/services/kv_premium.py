"""KV service for premium status caching."""

import json


class PremiumKVService:
    """Service for caching premium user status in Cloudflare KV."""
    
    def __init__(self, kv_namespace):
        self.kv = kv_namespace
        self.ttl = 86400  # 24 hours
    
    async def is_premium(self, user_id: str) -> bool:
        """Check if user is premium from KV cache.
        
        Returns False if not found (cache miss), caller should fallback to D1.
        """
        if not self.kv:
            return False
        
        try:
            value = await self.kv.get(f"premium:{user_id}")
            if value:
                data = json.loads(value)
                return data.get("is_premium", False)
        except Exception:
            pass
        return False
    
    async def set_premium(self, user_id: str, is_premium: bool) -> bool:
        """Set premium status in KV cache with TTL."""
        if not self.kv:
            return False
        
        try:
            await self.kv.put(
                f"premium:{user_id}",
                json.dumps({"is_premium": is_premium, "updated_at": int(__import__('time').time())}),
                expiration_ttl=self.ttl,
            )
            return True
        except Exception:
            return False
    
    async def invalidate(self, user_id: str) -> bool:
        """Invalidate premium status cache."""
        if not self.kv:
            return False
        
        try:
            await self.kv.delete(f"premium:{user_id}")
            return True
        except Exception:
            return False