import httpx, asyncio, uuid, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
url = os.getenv("SUPABASE_URL", "").rstrip("/")

async def main():
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    base = f"{url}/rest/v1"
    async with httpx.AsyncClient(base_url=base, headers=headers, timeout=15) as c:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "password_hash": "test",
            "name": "Test",
        }
        r = await c.post("/users", json=user)
        print(f"Create user: {r.status_code} {r.text[:100]}")
        
        vton = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "product_id": str(uuid.uuid4()),
            "input_image_url": "https://example.com/user.jpg",
            "garment_image_url": "https://example.com/garment.jpg",
            "status": "pending",
        }
        r2 = await c.post("/vton_results", json=vton)
        print(f"Create VTON: {r2.status_code}")
        print(f"Body: |{r2.text}|")

asyncio.run(main())
