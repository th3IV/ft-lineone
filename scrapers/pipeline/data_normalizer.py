from scrapers.models.product_dto import ProductDTO


_CATEGORY_MAP = {
    "ropa-mujer": "women-clothing",
    "ropa-hombre": "men-clothing",
    "zapatos": "footwear",
    "accesorios": "accessories",
    "deportes": "sports",
    "vestuario-mujer": "women-clothing",
    "vestuario-hombre": "men-clothing",
    "calzado": "footwear",
    "hombre": "men-clothing",
    "mujer": "women-clothing",
    "nino": "kids",
    "nina": "kids",
}

_SIZE_MAP = {
    "xs": "XS",
    "s": "S",
    "m": "M",
    "l": "L",
    "xl": "XL",
    "xxl": "XXL",
    "36": "36",
    "37": "37",
    "38": "38",
    "39": "39",
    "40": "40",
    "41": "41",
    "42": "42",
    "43": "43",
    "44": "44",
    "unico": "ONE_SIZE",
    "único": "ONE_SIZE",
}

_COLOR_MAP = {
    "negro": "black",
    "blanco": "white",
    "gris": "gray",
    "azul": "blue",
    "rojo": "red",
    "verde": "green",
    "amarillo": "yellow",
    "rosa": "pink",
    "cafe": "brown",
    "café": "brown",
    "beige": "beige",
    "naranjo": "orange",
    "morado": "purple",
    "dorado": "gold",
    "plateado": "silver",
}

_CURRENCY_RATES = {
    "CLP": 1.0,
    "USD": 950.0,
    "EUR": 1030.0,
    "ARS": 2.5,
    "PEN": 250.0,
}


class DataNormalizer:

    def normalize_product(self, raw_product: dict) -> ProductDTO:
        return ProductDTO(
            external_id=str(raw_product.get("external_id", "")),
            store=raw_product.get("store", ""),
            name=raw_product.get("name", ""),
            description=raw_product.get("description", ""),
            price=float(raw_product.get("price", 0.0)),
            currency=raw_product.get("currency", "CLP"),
            original_url=raw_product.get("original_url", ""),
            image_urls=raw_product.get("image_urls", []),
            category=self.standardize_category(raw_product.get("category", "")),
            sizes=[self.standardize_size(s) for s in raw_product.get("sizes", [])],
            colors=[self.standardize_color(c) for c in raw_product.get("colors", [])],
            availability=bool(raw_product.get("availability", True)),
        )

    def standardize_category(self, category: str) -> str:
        key = category.strip().lower().replace(" ", "-")
        return _CATEGORY_MAP.get(key, category)

    def standardize_size(self, size: str) -> str:
        key = size.strip().lower()
        return _SIZE_MAP.get(key, size)

    def standardize_color(self, color: str) -> str:
        key = color.strip().lower()
        return _COLOR_MAP.get(key, color)

    def convert_currency(self, amount: float, from_currency: str) -> float:
        from_rate = _CURRENCY_RATES.get(from_currency.upper(), 1.0)
        return amount * from_rate
