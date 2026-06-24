import sys; sys.path.insert(0, '.')
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    c = AsyncIOMotorClient('mongodb://localhost:27017')
    db = c['ft_lineone']
    count = await db['products'].count_documents({'store': 'zara'})
    print(f'Total Zara products: {count}')
    cursor = db['products'].find({'store': 'zara'}).limit(5)
    async for doc in cursor:
        img = doc.get('image_url', '') or ''
        print(f'  {doc.get("name","?")}')
        print(f'    image_url: {img[:100] if img else "MISSING"}')
        print(f'    price: {doc.get("price")}')
        print(f'    external_id: {doc.get("external_id")}')
    await c.close()

asyncio.run(check())
