from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, products, recommendations, users, vton

app = FastAPI(
    title="FT LineOne Backend",
    description="Fashion Technology backend with AI orchestration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(recommendations.router)
app.include_router(vton.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ft-lineone-backend"}
