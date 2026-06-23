import sys; sys.path.insert(0, '.')
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    c = AsyncIOMotorClient('mongodb://localhost:27017')
    dbs = await c.list_database_names()
    print(f'Databases: {dbs}')
    
    for db_name in dbs:
        if db_name in ['admin', 'config', 'local']:
            continue
        db = c[db_name]
        colls = await db.list_collection_names()
        print(f'  {db_name}: collections={colls}')
    
    c.close()

asyncio.run(check())
