from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
import asyncio
import random

from src.application.agents.skills.validate_product.schema import ValidateProductInput, RawProduct, ValidationResult
from src.application.agents.skills.normalize_product.schema import NormalizeProductInput, NormalizedProduct
from src.application.agents.skills.process_product_image.schema import ProcessImageInput, ProcessImageOutput
from src.application.agents.skills.validate_product.service import ValidateProductSkill
from src.application.agents.skills.normalize_product.service import NormalizeProductSkill
from src.application.agents.skills.process_product_image.service import ProcessProductImageSkill
from src.infrastructure.database.mongodb.repositories import MongoProductRepository
from src.infrastructure.database.mongodb.models import ProductDocument, ColorInfo as DocColorInfo, ProductImage as DocProductImage, ProductAttributes as DocProductAttributes


class BaseScraper(ABC):
    def __init__(self, store_name: str, base_url: str):
        self._store_name = store_name
        self._base_url = base_url
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-CL,es;q=0.9,en;q=0.5",
            },
        )
        self._validate_skill: ValidateProductSkill | None = None
        self._normalize_skill: NormalizeProductSkill | None = None
        self._image_skill: ProcessProductImageSkill | None = None
        self._repo: MongoProductRepository | None = None

    @property
    def store_name(self) -> str:
        return self._store_name

    @property
    def base_url(self) -> str:
        return self._base_url

    def set_skills(self, validate: ValidateProductSkill, normalize: NormalizeProductSkill, image: ProcessProductImageSkill, repo: MongoProductRepository):
        self._validate_skill = validate
        self._normalize_skill = normalize
        self._image_skill = image
        self._repo = repo

    @abstractmethod
    async def scrape_category(self, category: str, max_items: int) -> List[Dict[str, Any]]:
        pass

    async def _fetch_page(self, url: str) -> BeautifulSoup:
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Rate limiting
        response = await self._client.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    async def close(self):
        await self._client.aclose()

    def _to_document(self, normalized: NormalizedProduct) -> ProductDocument:
        return ProductDocument(
            external_id=normalized.external_id,
            store=normalized.store,
            slug=normalized.slug,
            name=normalized.name,
            description=normalized.description,
            price=normalized.price,
            currency=normalized.currency,
            category=normalized.category,
            subcategory=normalized.subcategory,
            sizes=normalized.sizes,
            colors=[DocColorInfo(name=c.name) for c in normalized.colors],
            images=[DocProductImage(url=img.url, width=img.width, height=img.height, is_primary=img.is_primary) for img in normalized.images],
            attributes=DocProductAttributes(
                fit=normalized.attributes.fit,
                material=normalized.attributes.material,
                occasion=normalized.attributes.occasion,
                season=normalized.attributes.season,
            ),
            product_url=normalized.product_url,
            scraped_at=normalized.scraped_at,
        )

    async def process_raw_products(self, raw_products: List[Dict[str, Any]]) -> dict:
        if not all([self._validate_skill, self._normalize_skill, self._image_skill, self._repo]):
            raise RuntimeError("Skills and repository not configured. Call set_skills() first.")

        saved = 0
        rejected = 0
        errors = []
        saved_ids = []

        for raw in raw_products:
            try:
                raw["store"] = self._store_name
                raw_product = RawProduct(**raw)
                validation = await self._validate_skill.execute(ValidateProductInput(product=raw_product))
                if not validation.valid:
                    rejected += 1
                    errors.append(f"{raw.get('external_id', 'unknown')}: {validation.reason}")
                    continue

                cleaned = validation.cleaned_product or raw_product
                normalized_result = await self._normalize_skill.execute(NormalizeProductInput(product=cleaned.model_dump()))
                normalized = normalized_result.normalized
                image_result = await self._image_skill.execute(ProcessImageInput(
                    external_id=normalized.external_id,
                    store=self._store_name,
                    image_url=normalized.images[0].url if normalized.images else "",
                    is_primary=True,
                ))

                normalized.images = image_result.images
                doc = self._to_document(normalized)
                await self._repo.save(doc)
                saved += 1
                saved_ids.append(normalized.external_id)

            except Exception as e:
                rejected += 1
                errors.append(f"{raw.get('external_id', 'unknown')}: {str(e)}")

        return {"saved": saved, "rejected": rejected, "errors": errors, "products": saved_ids}