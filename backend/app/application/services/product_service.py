from datetime import datetime, timezone
from math import ceil

from app.domain.models.product import Product
from app.infrastructure.persistence.postgres.repositories.product_repository import (
    ProductRepository,
)

MOCK_PRODUCTS = [
    Product(
        id="mock-001", external_id="ext-001", store="Falabella", name="Polera Algodón Premium",
        description="Polera de algodón orgánico de corte regular. Ideal para uso diario.",
        price=15990, currency="CLP", image_url="https://picsum.photos/seed/polera1/400/500",
        category="Poleras", sizes=["S", "M", "L", "XL"], colors=["Negro", "Blanco", "Azul Marino"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-002", external_id="ext-002", store="Ripley", name="Jeans Rectos Hombre",
        description="Jeans de corte recto en denim elástico. Cómodos y duraderos.",
        price=24990, currency="CLP", image_url="https://picsum.photos/seed/jeans1/400/500",
        category="Pantalones", sizes=["30", "32", "34", "36"], colors=["Azul", "Negro", "Gris"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-003", external_id="ext-003", store="Paris", name="Chaqueta Cuero Sintético",
        description="Chaqueta de cuero sintético con forro interior. Estilo motoquero.",
        price=45990, currency="CLP", image_url="https://picsum.photos/seed/chaqueta1/400/500",
        category="Chaquetas", sizes=["M", "L", "XL"], colors=["Negro", "Marrón"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-004", external_id="ext-004", store="Maui", name="Vestido Floral Verano",
        description="Vestido ligero con estampado floral. Perfecto para días cálidos.",
        price=19990, currency="CLP", image_url="https://picsum.photos/seed/vestido1/400/500",
        category="Vestidos", sizes=["S", "M", "L"], colors=["Rojo", "Azul", "Blanco"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-005", external_id="ext-005", store="Zara", name="Camisa Blanca Clásica",
        description="Camisa de vestir blanca en algodón premium. Corte slim fit.",
        price=22990, currency="CLP", image_url="https://picsum.photos/seed/camisa1/400/500",
        category="Camisas", sizes=["S", "M", "L", "XL", "XXL"], colors=["Blanco", "Celeste"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-006", external_id="ext-006", store="Falabella", name="Short Deportivo Hombre",
        description="Short de running con bolsillos y cintura elástica.",
        price=9990, currency="CLP", image_url="https://picsum.photos/seed/short1/400/500",
        category="Shorts", sizes=["S", "M", "L", "XL"], colors=["Negro", "Gris", "Azul"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-007", external_id="ext-007", store="Ripley", name="Polerón Oversize",
        description="Polerón de algodón con capucha y bolsillo frontal. Estilo urbano.",
        price=29990, currency="CLP", image_url="https://picsum.photos/seed/poleron1/400/500",
        category="Polerones", sizes=["M", "L", "XL", "XXL"], colors=["Gris", "Negro", "Verde Oliva"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-008", external_id="ext-008", store="Paris", name="Falda Plizada Mujer",
        description="Falda plizada larga con cintura alta. Elegante y versátil.",
        price=17990, currency="CLP", image_url="https://picsum.photos/seed/falda1/400/500",
        category="Faldas", sizes=["S", "M", "L"], colors=["Negro", "Beige", "Rosado"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-009", external_id="ext-009", store="Maui", name="Zapatillas Urbanas",
        description="Zapatillas casual con suela cushlon. Diseño minimalista.",
        price=34990, currency="CLP", image_url="https://picsum.photos/seed/zapa1/400/500",
        category="Calzado", sizes=["38", "39", "40", "41", "42", "43"], colors=["Blanco", "Negro"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-010", external_id="ext-010", store="Zara", name="Blazer Slim Fit",
        description="Blazer de vestir en tejido mezcla lana. Corte slim fit italiano.",
        price=54990, currency="CLP", image_url="https://picsum.photos/seed/blazer1/400/500",
        category="Chaquetas", sizes=["S", "M", "L", "XL"], colors=["Negro", "Gris Carbón"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-011", external_id="ext-011", store="Falabella", name="Polera Estampada",
        description="Polera con estampado gráfico exclusivo. Algodón peinado 180g.",
        price=12990, currency="CLP", image_url="https://picsum.photos/seed/polera2/400/500",
        category="Poleras", sizes=["S", "M", "L", "XL"], colors=["Blanco", "Negro", "Rojo"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-012", external_id="ext-012", store="Ripley", name="Pantalón Cargo",
        description="Pantalón cargo con múltiples bolsillos. Tela resistente y cómoda.",
        price=27990, currency="CLP", image_url="https://picsum.photos/seed/cargo1/400/500",
        category="Pantalones", sizes=["30", "32", "34", "36"], colors=["Verde Oliva", "Negro", "Beige"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-013", external_id="ext-013", store="Paris", name="Vestido Noche Elegante",
        description="Vestido largo de gala con escote V y detalles en pedrería.",
        price=59990, currency="CLP", image_url="https://picsum.photos/seed/vestido2/400/500",
        category="Vestidos", sizes=["S", "M", "L"], colors=["Negro", "Rojo", "Azul Noche"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-014", external_id="ext-014", store="Zara", name="Camisa Linda Premium",
        description="Camisa de lino premium con botones de concha. Fresca y elegante.",
        price=32990, currency="CLP", image_url="https://picsum.photos/seed/camisa2/400/500",
        category="Camisas", sizes=["S", "M", "L", "XL"], colors=["Blanco", "Celeste", "Rosa"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-015", external_id="ext-015", store="Maui", name="Parka Invierno",
        description="Parka acolchada con capucha desmontable. Resistente al agua.",
        price=69990, currency="CLP", image_url="https://picsum.photos/seed/parka1/400/500",
        category="Chaquetas", sizes=["M", "L", "XL", "XXL"], colors=["Negro", "Verde Militar", "Azul"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-016", external_id="ext-016", store="Falabella", name="Polerón Cremallera",
        description="Polerón con cremallera completa y bolsillos laterales. Algodón fleece.",
        price=25990, currency="CLP", image_url="https://picsum.photos/seed/poleron2/400/500",
        category="Polerones", sizes=["S", "M", "L", "XL"], colors=["Gris", "Azul Marino", "Negro"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-017", external_id="ext-017", store="Ripley", name="Botines Cuero Mujer",
        description="Botines de cuero genuino con taco block. Suela antideslizante.",
        price=45990, currency="CLP", image_url="https://picsum.photos/seed/botin1/400/500",
        category="Calzado", sizes=["36", "37", "38", "39", "40"], colors=["Negro", "Marrón"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-018", external_id="ext-018", store="Paris", name="Short Mujer Denim",
        description="Short de jean con dobladillo desfilado. Tiro alto y cómodo.",
        price=14990, currency="CLP", image_url="https://picsum.photos/seed/short2/400/500",
        category="Shorts", sizes=["S", "M", "L"], colors=["Azul", "Negro", "Blanco"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-019", external_id="ext-019", store="Maui", name="Accesorio Mochila Urbana",
        description="Mochila impermeable con compartidor para notebook 15\". 25L.",
        price=24990, currency="CLP", image_url="https://picsum.photos/seed/mochila1/400/500",
        category="Accesorios", sizes=["Único"], colors=["Negro", "Gris", "Verde"],
        scraped_at=datetime.now(timezone.utc),
    ),
    Product(
        id="mock-020", external_id="ext-020", store="Zara", name="Falda Mini Plizada",
        description="Falda mini plizada con pretina ancha. Estilo colegial moderno.",
        price=15990, currency="CLP", image_url="https://picsum.photos/seed/falda2/400/500",
        category="Faldas", sizes=["XS", "S", "M", "L"], colors=["Negro", "Blanco", "Rosado"],
        scraped_at=datetime.now(timezone.utc),
    ),
]

MOCK_GENDERS = {
    "Hombre": ["mock-001", "mock-002", "mock-005", "mock-006", "mock-007", "mock-010", "mock-011", "mock-012", "mock-014", "mock-016"],
    "Mujer": ["mock-004", "mock-008", "mock-013", "mock-017", "mock-018", "mock-020"],
    "Unisex": ["mock-003", "mock-009", "mock-015", "mock-019"],
}

MOCK_ID_MAP = {p.id: p for p in MOCK_PRODUCTS}


def _filter_mock(filters: dict) -> list[Product]:
    results = list(MOCK_PRODUCTS)

    if filters.get("gender") in MOCK_GENDERS:
        valid_ids = MOCK_GENDERS[filters["gender"]]
        results = [p for p in results if p.id in valid_ids]

    if filters.get("clothingType"):
        types = filters["clothingType"] if isinstance(filters["clothingType"], list) else [filters["clothingType"]]
        results = [p for p in results if p.category in types]

    if filters.get("size"):
        results = [p for p in results if filters["size"] in p.sizes]

    if filters.get("color"):
        results = [p for p in results if filters["color"] in p.colors]

    if filters.get("store"):
        results = [p for p in results if p.store.lower() == filters["store"].lower()]

    if filters.get("minPrice"):
        results = [p for p in results if p.price >= float(filters["minPrice"])]

    if filters.get("maxPrice"):
        results = [p for p in results if p.price <= float(filters["maxPrice"])]

    if filters.get("query"):
        q = filters["query"].lower()
        results = [p for p in results if q in p.name.lower() or q in p.description.lower()]

    return results


class ProductService:
    def __init__(self, product_repo: ProductRepository | None = None):
        self._product_repo = product_repo or ProductRepository()
        self._mock_enabled = True

    async def _should_use_mock(self) -> bool:
        if not self._mock_enabled:
            return False
        try:
            products, _ = await self._product_repo.find_all(page=1, per_page=1)
            return len(products) == 0
        except Exception:
            return True

    async def get_catalog(self, page: int = 1, per_page: int = 20, filters: dict | None = None) -> tuple[list[Product], int]:
        if await self._should_use_mock():
            filtered = _filter_mock(filters or {})
            total = len(filtered)
            offset = (page - 1) * per_page
            return filtered[offset:offset + per_page], total
        repo_filters = filters or {}
        if "gender" in repo_filters:
            del repo_filters["gender"]
        if "clothingType" in repo_filters:
            del repo_filters["clothingType"]
        return await self._product_repo.find_all(page=page, per_page=per_page)

    async def get_by_id(self, product_id: str) -> Product | None:
        if await self._should_use_mock():
            return MOCK_ID_MAP.get(product_id)
        return await self._product_repo.find_by_id(product_id)

    async def search(self, query: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        if await self._should_use_mock():
            results = [p for p in MOCK_PRODUCTS if query.lower() in p.name.lower() or query.lower() in p.description.lower()]
            total = len(results)
            offset = (page - 1) * per_page
            return results[offset:offset + per_page], total
        return await self._product_repo.search(query=query, page=page, per_page=per_page)

    async def get_by_store(self, store: str, page: int = 1, per_page: int = 20) -> tuple[list[Product], int]:
        if await self._should_use_mock():
            results = [p for p in MOCK_PRODUCTS if p.store.lower() == store.lower()]
            total = len(results)
            offset = (page - 1) * per_page
            return results[offset:offset + per_page], total
        return await self._product_repo.find_by_store(store=store, page=page, per_page=per_page)
