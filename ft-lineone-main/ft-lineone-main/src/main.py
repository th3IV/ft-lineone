import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.infrastructure.database.mongodb.client import MongoDBClient
from src.infrastructure.database.postgres.supabase_rest_client import SupabaseRestClient
from src.infrastructure.external_services.grok_client import GrokClient
from src.infrastructure.external_services.cloudinary_client import CloudinaryClient
from src.infrastructure.external_services.hf_vton_client import HFVTONClient
from src.infrastructure.external_services.genlook_client import GenlookVTONClient
from src.infrastructure.database.mongodb.repositories import MongoProductRepository
from src.infrastructure.database.postgres.repositories import VTONRepository
from src.infrastructure.scrapers.pipeline import ScraperPipeline
from src.infrastructure.scrapers.scheduler import ScraperScheduler
from src.infrastructure.scrapers.zara_scraper import ZaraScraper
from src.infrastructure.database.mongodb.models import ProductDocument, ProductImage
from src.application.agents.skills.validate_product.service import ValidateProductSkill
from src.application.agents.skills.normalize_product.service import NormalizeProductSkill
from src.application.agents.skills.process_product_image.service import ProcessProductImageSkill
from src.application.agents.skills.virtual_try_on.service import VTONSkill
from src.application.agents.skills.recommend_products.service import RecommendProductsSkill
from src.application.agents.fashion_advisor_agent import FashionAdvisorAgent
from src.application.agents.skills.recommend_products.schema import UserProfile, UserBodyMeasurements
from src.api.v1.routes import auth_router


grok_client: GrokClient | None = None
cloudinary_client: CloudinaryClient | None = None
hf_vton_client: HFVTONClient | None = None
genlook_vton_client: GenlookVTONClient | None = None
mongo_repo: MongoProductRepository | None = None
vton_repo: VTONRepository | None = None
scraper_pipeline: ScraperPipeline | None = None
scraper_scheduler: ScraperScheduler | None = None
vton_skill: VTONSkill | None = None
recommend_skill: RecommendProductsSkill | None = None
advisor_agent: FashionAdvisorAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global grok_client, cloudinary_client, hf_vton_client, genlook_vton_client, mongo_repo, vton_repo, scraper_pipeline, scraper_scheduler, vton_skill, recommend_skill, advisor_agent

    try:
        await MongoDBClient.connect()
    except Exception as e:
        print(f"[WARN] MongoDB no disponible: {e}")
    SupabaseRestClient.initialize()

    grok_client = GrokClient()
    cloudinary_client = CloudinaryClient()
    hf_vton_client = HFVTONClient()
    genlook_vton_client = GenlookVTONClient()
    try:
        mongo_repo = MongoProductRepository()
        await mongo_repo.initialize()
    except Exception as e:
        print(f"[WARN] MongoProductRepository no disponible: {e}")
        mongo_repo = None
    vton_repo = VTONRepository()

    validate_skill = ValidateProductSkill(grok_client)
    normalize_skill = NormalizeProductSkill(grok_client)
    image_skill = ProcessProductImageSkill(cloudinary_client)
    vton_skill = VTONSkill(grok_client=grok_client, hf_client=hf_vton_client, cloudinary_client=cloudinary_client, genlook_client=genlook_vton_client)
    recommend_skill = RecommendProductsSkill(grok_client)
    if mongo_repo:
        advisor_agent = FashionAdvisorAgent(
            grok_client=grok_client,
            recommend_skill=recommend_skill,
            vton_skill=vton_skill,
            product_repo=mongo_repo,
        )
    else:
        advisor_agent = None
        print("[WARN] Advisor agent deshabilitado por falta de MongoDB")

    if mongo_repo:
        scraper_pipeline = ScraperPipeline(
            grok_client=grok_client,
            cloudinary_client=cloudinary_client,
            mongo_repo=mongo_repo,
        )
        scraper_scheduler = ScraperScheduler(scraper_pipeline)
        if settings.ENVIRONMENT == "production":
            scraper_scheduler.start()
    else:
        scraper_pipeline = None
        scraper_scheduler = None
        print("[WARN] Scraping deshabilitado por falta de MongoDB")

    yield

    if scraper_scheduler:
        scraper_scheduler.stop()
    try:
        await MongoDBClient.close()
    except Exception:
        pass
    SupabaseRestClient._client = None


app = FastAPI(
    title="FT LineOne Backend",
    description="Fashion Technology backend with AI orchestration - Free Tier MVP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ft-lineone-backend",
        "version": "1.0.0",
        "grok_available": grok_client._available if grok_client else False,
        "mongodb_available": mongo_repo is not None,
    }


@app.get("/api/v1/products")
async def list_products(page: int = 1, per_page: int = 20, store: str | None = None, category: str | None = None):
    if not mongo_repo:
        return {"products": [], "total": 0, "page": page, "per_page": per_page}

    if store:
        products = await mongo_repo.find_by_store(store, page, per_page)
        total = len(products)
    elif category:
        products = await mongo_repo.find_by_category(category, page, per_page)
        total = len(products)
    else:
        products, total = await mongo_repo.find_all(page, per_page)

    return {
        "products": [_product_with_image_url(p) for p in products],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def _product_with_image_url(p):
    d = p.model_dump()
    d["id"] = str(p.id)
    d["image_url"] = d["images"][0]["url"] if d.get("images") else ""
    return d


@app.get("/api/v1/products/search")
async def search_products(q: str, page: int = 1, per_page: int = 20):
    if not mongo_repo:
        return {"products": [], "total": 0}

    products = await mongo_repo.search(q, page, per_page)
    return {"products": [_product_with_image_url(p) for p in products], "total": len(products)}


@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: str):
    if not mongo_repo:
        return {"error": "MongoDB not available"}

    from src.infrastructure.database.mongodb.models import ProductDocument
    product = await ProductDocument.get(product_id)
    if not product:
        return {"error": "Product not found"}
    return _product_with_image_url(product)


@app.get("/api/v1/recommendations")
async def get_recommendations(
    user_id: str,
    preferences: str | None = None,
    favorite_colors: str | None = None,
    height: int | None = None,
    weight: int | None = None,
    size_top: str | None = None,
    size_bottom: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    style_notes: str | None = None,
    limit: int = 10,
):
    if not recommend_skill or not mongo_repo:
        return {"error": "Recommendations not available"}

    products, _ = await mongo_repo.find_all(page=1, per_page=50)

    from src.application.agents.skills.recommend_products.schema import (
        UserProfile, UserBodyMeasurements, RecommendProductsInput,
        ProductSummary, ProductColor, ProductImage, ProductAttributes,
    )

    user_profile = UserProfile(
        user_id=user_id,
        body_measurements=UserBodyMeasurements(
            height=height,
            weight=weight,
            size_top=size_top,
            size_bottom=size_bottom,
        ),
        preferences=preferences.split(",") if preferences else [],
        favorite_colors=favorite_colors.split(",") if favorite_colors else [],
        price_range={"min": price_min, "max": price_max} if price_min or price_max else None,
        style_notes=style_notes or "",
    )

    product_summaries = [
        ProductSummary(
            external_id=p.external_id,
            store=p.store,
            slug=p.slug,
            name=p.name,
            description=p.description,
            price=p.price,
            currency=p.currency,
            category=p.category,
            subcategory=p.subcategory,
            sizes=p.sizes,
            colors=[ProductColor(name=c.name) for c in p.colors],
            images=[ProductImage(url=img.url, width=img.width, height=img.height, is_primary=img.is_primary) for img in p.images],
            attributes=ProductAttributes(
                fit=p.attributes.fit,
                material=p.attributes.material,
                occasion=p.attributes.occasion,
                season=p.attributes.season,
            ),
        )
        for p in products
    ]

    input_data = RecommendProductsInput(
        user_profile=user_profile,
        products=product_summaries,
        limit=limit,
    )
    result = await recommend_skill.execute(input_data)
    return {"recommendations": [r.model_dump() for r in result.recommendations]}


@app.get("/scrape/{store}")
async def trigger_scrape(store: str, categories: str | None = None, max_per_category: int = 20):
    if not scraper_pipeline:
        return {"success": False, "error": "Pipeline not initialized"}

    cat_list = categories.split(",") if categories else None
    result = await scraper_pipeline.run_scraper(store, cat_list, max_per_category)
    return result


@app.post("/scrape/all")
async def trigger_scrape_all(categories: str | None = None, max_per_category: int = 20):
    if not scraper_pipeline:
        return {"success": False, "error": "Pipeline not initialized"}

    cat_list = categories.split(",") if categories else None
    result = await scraper_pipeline.run_all_stores(cat_list, max_per_category)
    return result


@app.get("/scrape/zara/direct")
async def trigger_zara_scrape_direct(max_per_category: int = 10):
    if not mongo_repo:
        return {"success": False, "error": "MongoDB not initialized"}

    scraper = ZaraScraper()
    try:
        from src.infrastructure.scrapers.pipeline import ScraperPipeline
        categories = ScraperPipeline.CATEGORIES
        all_saved = 0
        results = []

        for category in categories:
            products = await scraper.scrape_category(category, max_per_category)
            for p in products:
                doc = ProductDocument(
                    external_id=p["external_id"],
                    store="zara",
                    slug=p["external_id"],
                    name=p["name"],
                    description=p.get("name", ""),
                    price=round(p["price"], 2),
                    currency="CLP",
                    category=p.get("category", category),
                    product_url=p["product_url"],
                    scraped_at=datetime.utcnow(),
                )
                if p.get("image_url"):
                    doc.images = [ProductImage(url=p["image_url"], is_primary=True)]
                await mongo_repo.save(doc)
                all_saved += 1

            results.append({"category": category, "count": len(products)})

        return {"success": True, "saved": all_saved, "categories": results}
    finally:
        await scraper.close()


@app.post("/vton/try-on")
async def vton_try_on(
    user_image: UploadFile = File(...),
    product_id: str = Form(...),
):
    if not vton_skill:
        return {"success": False, "error": "VTON skill not initialized"}

    from src.infrastructure.database.mongodb.models import ProductDocument
    product = await ProductDocument.get(product_id)
    if not product:
        return {"success": False, "error": "Product not found"}

    product_image_url = product.images[0].url if product.images else ""
    user_image_bytes = await user_image.read()

    from src.application.agents.skills.virtual_try_on.schema import VTONSkillInput
    input_data = VTONSkillInput(
        user_id="frontend_user",
        product_id=product_id,
        product_image_url=product_image_url,
    )
    result = await vton_skill.execute(input_data, user_image_bytes=user_image_bytes)
    return result.model_dump()


@app.get("/vton/result/{job_id}")
async def vton_get_result(job_id: str):
    if not vton_repo:
        return {"success": False, "error": "VTON repo not initialized"}

    result = await vton_repo.find_by_id(job_id)
    if not result:
        return {"success": False, "error": "Job not found"}

    return {
        "job_id": result["id"],
        "status": result["status"],
        "result_url": result["output_image_url"],
        "error": result["error"],
        "created_at": result["created_at"],
    }


@app.get("/vton/history")
async def vton_history(user_id: str = "", limit: int = 20):
    if not vton_repo:
        return {"success": False, "error": "VTON repo not initialized"}

    results = await vton_repo.find_by_user(user_id, limit)
    return [
        {
            "job_id": r["id"],
            "product_id": r["product_id"],
            "status": r["status"],
            "result_url": r["output_image_url"],
            "created_at": r["created_at"],
        }
        for r in results
    ]


@app.post("/advisor/chat")
async def advisor_chat(
    user_id: str,
    message: str,
    height: int | None = None,
    weight: int | None = None,
    size_top: str | None = None,
    size_bottom: str | None = None,
    preferences: str | None = None,
    favorite_colors: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    style_notes: str | None = None,
    context: str | None = None,
):
    if not advisor_agent:
        return {"success": False, "error": "Advisor agent not initialized"}

    import json
    ctx = json.loads(context) if context else {}

    user_profile = UserProfile(
        user_id=user_id,
        body_measurements=UserBodyMeasurements(
            height=height,
            weight=weight,
            size_top=size_top,
            size_bottom=size_bottom,
        ),
        preferences=preferences.split(",") if preferences else [],
        favorite_colors=favorite_colors.split(",") if favorite_colors else [],
        price_range={"min": price_min, "max": price_max} if price_min or price_max else None,
        style_notes=style_notes or "",
    )

    result = await advisor_agent.process_message(user_id, message, user_profile, ctx)
    return result