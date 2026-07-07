"""Cloudflare D1 Database Service using native D1 bindings."""

import json
from datetime import datetime
from typing import Optional
import uuid


class UserModel:
    """User data model (D1 row)."""

    def __init__(self, row: dict):
        self.id = row.get("id", str(uuid.uuid4()))
        self.email = row.get("email", "")
        self.name = row.get("name", "")
        self.password_hash = row.get("password_hash", "")
        self.body_measurements = (
            json.loads(row["body_measurements"])
            if isinstance(row.get("body_measurements"), str)
            else (row.get("body_measurements") or None)
        )
        self.preferences = (
            json.loads(row["preferences"])
            if isinstance(row.get("preferences"), str)
            else (row.get("preferences") or {})
        )
        self.profile_image = row.get("profile_image")
        self.created_at = row.get("created_at", datetime.utcnow().isoformat())


class ProductModel:
    """Product data model (D1 row)."""

    def __init__(self, row: dict):
        self.id = row.get("id", str(uuid.uuid4()))
        self.external_id = row.get("external_id", "")
        self.name = row.get("name", "")
        self.store = row.get("store", "")
        self.price = float(row.get("price", 0))
        self.currency = row.get("currency", "CLP")
        self.category = row.get("category", "")
        self.description = row.get("description", "")
        self.original_url = row.get("original_url", "")
        self.image_url = row.get("image_url")
        self.image_urls = (
            json.loads(row["image_urls"])
            if isinstance(row.get("image_urls"), str)
            else (row.get("image_urls") or [])
        )
        self.sizes = (
            json.loads(row["sizes"])
            if isinstance(row.get("sizes"), str)
            else (row.get("sizes") or [])
        )
        self.colors = (
            json.loads(row["colors"])
            if isinstance(row.get("colors"), str)
            else (row.get("colors") or [])
        )
        self.availability = bool(row.get("availability", 1))
        self.created_at = row.get("created_at", datetime.utcnow().isoformat())


class VtonResultModel:
    """VTON result data model (D1 row)."""

    def __init__(self, row: dict):
        self.id = row.get("id", str(uuid.uuid4()))
        self.user_id = row.get("user_id", "")
        self.product_id = row.get("product_id", "")
        self.status = row.get("status", "pending")
        self.input_image_url = row.get("input_image_url")
        self.output_image_url = row.get("output_image_url")
        self.garment_image_url = row.get("garment_image_url")
        self.error_message = row.get("error_message")
        self.youcam_task_id = row.get("youcam_task_id")
        self.created_at = row.get("created_at", datetime.utcnow().isoformat())
        self.completed_at = row.get("completed_at")


class DatabaseService:
    """D1 Database service using native D1 binding API."""

    def __init__(self, env):
        """Initialize with Cloudflare Workers env."""
        self.env = env
        self.db = env.DB  # D1 binding from wrangler

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        result = await self.db.prepare(
            "SELECT * FROM users WHERE email = ? LIMIT 1"
        ).bind(email).first()
        if result:
            return UserModel(result)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID."""
        result = await self.db.prepare(
            "SELECT * FROM users WHERE id = ? LIMIT 1"
        ).bind(user_id).first()
        if result:
            return UserModel(result)
        return None

    async def create_user(self, user_data: dict) -> UserModel:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self.db.prepare(
            """INSERT INTO users (id, email, name, password_hash, body_measurements, preferences, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            user_id,
            user_data["email"],
            user_data["name"],
            user_data["password_hash"],
            json.dumps(user_data.get("body_measurements")) if user_data.get("body_measurements") else None,
            json.dumps(user_data.get("preferences", [])),
            now,
        ).run()

        return UserModel({
            "id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "password_hash": user_data["password_hash"],
            "body_measurements": user_data.get("body_measurements"),
            "preferences": user_data.get("preferences", []),
            "created_at": now,
        })

    async def update_user(self, user_id: str, updates: dict) -> bool:
        """Update user fields. Supports: name, email, body_measurements, preferences, profile_image."""
        set_clauses = []
        params = []
        for key, value in updates.items():
            if key in ("name", "email", "profile_image"):
                set_clauses.append(f"{key} = ?")
                params.append(value)
            elif key == "body_measurements":
                set_clauses.append("body_measurements = ?")
                params.append(json.dumps(value))
            elif key == "preferences":
                set_clauses.append("preferences = ?")
                params.append(json.dumps(value))
        if not set_clauses:
            return False
        params.append(user_id)
        await self.db.prepare(
            f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        ).bind(*params).run()
        return True

    async def get_product(self, product_id: str) -> Optional[ProductModel]:
        """Get product by ID."""
        result = await self.db.prepare(
            "SELECT * FROM products WHERE id = ? LIMIT 1"
        ).bind(product_id).first()
        if result:
            return ProductModel(result)
        return None

    # Gender value → list of SQL LIKE keywords to match in category column
    GENDER_VARIANTS = {
        "hombre": ["hombre", "men", "masculino", "male"],
        "mujer": ["mujer", "women", "femenino", "female", "ladies", "damas"],
    }

    # Keywords that identify footwear (excluded from catalog — VTON doesn't support it)
    EXCLUDED_FOOTWEAR_KEYWORDS = [
        "calzado", "zapato", "zapatill", "sneaker", "tenis", "bota", "botin",
    ]

    # Frontend clothing type label → SQL LIKE keywords for category column
    CLOTHING_TYPE_MAP = {
        "Poleras": ["polera", "camiseta"],
        "Camisas": ["camisa"],
        "Pantalones": ["pantalon", "jean", "trouser", "pantalón"],
        "Shorts": ["short", "bermuda"],
        "Chaquetas": ["chaqueta", "parka", "abrigo", "cazadora"],
        "Vestidos": ["vestido", "mono"],
        "Faldas": ["falda"],
        "Polerones": ["polerón", "buzo", "sudadera"],
    }

    async def get_products(self, filters: dict, page: int = 1, limit: int = 20):
        """Get products with filters.

        Clothing type and gender filters use OR across keywords and are
        case-insensitive.  Multi-select values (comma-separated) are also
        handled via OR so that "Poleras,Vestidos" matches either keyword.
        """
        conditions = []
        params = []

        if filters.get("store"):
            conditions.append("store = ?")
            params.append(filters["store"])
        if filters.get("category"):
            conditions.append("LOWER(category) LIKE LOWER(?)")
            params.append(f"%{filters['category']}%")
        if filters.get("min_price") is not None:
            conditions.append("price >= ?")
            params.append(float(filters["min_price"]))
        if filters.get("max_price") is not None:
            conditions.append("price <= ?")
            params.append(float(filters["max_price"]))
        if filters.get("query"):
            conditions.append("name LIKE ?")
            params.append(f"%{filters['query']}%")

        # Gender filter — normalize variants and match any
        if filters.get("gender"):
            gender_values = [g.strip().lower() for g in filters["gender"].split(",") if g.strip()]
            if gender_values:
                gender_conds = []
                for gv in gender_values:
                    variants = self.GENDER_VARIANTS.get(gv, [gv])
                    for v in variants:
                        gender_conds.append("LOWER(category) LIKE ?")
                        params.append(f"%{v}%")
                conditions.append(f"({' OR '.join(gender_conds)})")

        # Clothing type filter — map frontend labels to SQL LIKE keywords
        if filters.get("clothing_type"):
            ct_values = [c.strip() for c in filters["clothing_type"].split(",") if c.strip()]
            ct_keywords = []
            for ct in ct_values:
                keywords = self.CLOTHING_TYPE_MAP.get(ct, [ct.lower()])
                ct_keywords.extend(keywords)
            if ct_keywords:
                ct_conds = []
                for kw in ct_keywords:
                    ct_conds.append("LOWER(category) LIKE ?")
                    params.append(f"%{kw}%")
                conditions.append(f"({' OR '.join(ct_conds)})")

        # Size filter: stored in JSON array column
        if filters.get("size"):
            conditions.append("sizes LIKE ?")
            params.append(f'%"{filters["size"]}"%')
        # Color filter: stored in JSON array column
        if filters.get("color"):
            conditions.append("colors LIKE ?")
            params.append(f'%"{filters["color"]}"%')

        # Exclude footwear from catalog (VTON doesn't support shoes)
        for kw in self.EXCLUDED_FOOTWEAR_KEYWORDS:
            conditions.append(f"LOWER(category) NOT LIKE '%{kw}%'")
            conditions.append(f"LOWER(name) NOT LIKE '%{kw}%'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Sort order
        sort_clause = "ORDER BY created_at DESC"
        if filters.get("sort") == "price_asc":
            sort_clause = "ORDER BY price ASC"
        elif filters.get("sort") == "price_desc":
            sort_clause = "ORDER BY price DESC"

        # Count total
        count_result = await self.db.prepare(
            f"SELECT COUNT(*) as total FROM products WHERE {where_clause}"
        ).bind(*params).first()
        total = count_result["total"] if count_result else 0

        # Fetch page
        offset = (page - 1) * limit
        d1_result = await self.db.prepare(
            f"SELECT * FROM products WHERE {where_clause} {sort_clause} LIMIT ? OFFSET ?"
        ).bind(*params, limit, offset).all()

        rows = d1_result.get("results", []) if isinstance(d1_result, dict) else d1_result
        products = [ProductModel(row) for row in rows]
        return products, total

    async def create_product(self, product_data: dict) -> ProductModel:
        """Create a new product."""
        product_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self.db.prepare(
            """INSERT OR IGNORE INTO products
               (id, external_id, name, store, price, currency, category, description,
                original_url, image_url, image_urls, sizes, colors, availability, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            product_id,
            product_data["external_id"],
            product_data["name"],
            product_data["store"],
            product_data["price"],
            product_data.get("currency", "CLP"),
            product_data.get("category", ""),
            product_data.get("description", ""),
            product_data.get("original_url", ""),
            product_data.get("image_url"),
            json.dumps(product_data.get("image_urls", [])),
            json.dumps(product_data.get("sizes", [])),
            json.dumps(product_data.get("colors", [])),
            1 if product_data.get("availability", True) else 0,
            now,
        ).run()

        return ProductModel({
            "id": product_id,
            "external_id": product_data["external_id"],
            "name": product_data["name"],
            "store": product_data["store"],
            "price": product_data["price"],
            "currency": product_data.get("currency", "CLP"),
            "category": product_data.get("category", ""),
            "description": product_data.get("description", ""),
            "original_url": product_data.get("original_url", ""),
            "image_url": product_data.get("image_url"),
            "image_urls": product_data.get("image_urls", []),
            "sizes": product_data.get("sizes", []),
            "colors": product_data.get("colors", []),
            "availability": product_data.get("availability", True),
            "created_at": now,
        })

    async def delete_products_by_store(self, store: str) -> int:
        """Delete all products from a specific store. Returns number of deleted products."""
        result = await self.db.prepare(
            "DELETE FROM products WHERE store = ?"
        ).bind(store).run()
        return result.changes if hasattr(result, 'changes') else 0

    async def update_product_sizes(self, product_id: str, sizes: list[str], colors: list[str] = None) -> bool:
        """Update sizes and optionally colors for an existing product."""
        sets = []
        params = []
        if sizes:
            sets.append("sizes = ?")
            params.append(json.dumps(sizes))
        if colors is not None:
            sets.append("colors = ?")
            params.append(json.dumps(colors))
        if not sets:
            return False
        params.append(product_id)
        await self.db.prepare(
            f"UPDATE products SET {', '.join(sets)} WHERE id = ?"
        ).bind(*params).run()
        return True

    async def get_products_without_sizes(self, store: str, limit: int = 100) -> list[ProductModel]:
        """Get products from a store that have empty sizes."""
        d1_result = await self.db.prepare(
            "SELECT * FROM products WHERE store = ? AND (sizes IS NULL OR sizes = '[]') LIMIT ?"
        ).bind(store, limit).all()
        rows = d1_result.get("results", []) if isinstance(d1_result, dict) else d1_result
        return [ProductModel(row) for row in rows]

    async def create_vton_result(self, data: dict) -> VtonResultModel:
        """Create a VTON result record."""
        vton_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self.db.prepare(
            """INSERT INTO vton_results
               (id, user_id, product_id, status, input_image_url, output_image_url, garment_image_url, error_message, youcam_task_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            vton_id,
            data["user_id"],
            data["product_id"],
            data.get("status", "pending"),
            data.get("input_image_url"),
            data.get("output_image_url"),
            data.get("garment_image_url"),
            data.get("error_message"),
            data.get("youcam_task_id"),
            now,
        ).run()

        return VtonResultModel({**data, "id": vton_id, "created_at": now})

    async def get_vton_result(self, vton_id: str) -> Optional[VtonResultModel]:
        """Get VTON result by ID."""
        result = await self.db.prepare(
            "SELECT * FROM vton_results WHERE id = ? LIMIT 1"
        ).bind(vton_id).first()
        if result:
            return VtonResultModel(result)
        return None

    async def get_vton_history(self, user_id: str, limit: int = 20) -> list[VtonResultModel]:
        """Get VTON history for a user."""
        d1_result = await self.db.prepare(
            "SELECT * FROM vton_results WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
        ).bind(user_id, limit).all()
        rows = d1_result.get("results", []) if isinstance(d1_result, dict) else d1_result
        return [VtonResultModel(row) for row in rows]

    async def update_vton_result(self, vton_id: str, data: dict) -> Optional[VtonResultModel]:
        """Update a VTON result record."""
        sets = []
        params = []
        for key in ("status", "output_image_url", "error_message", "completed_at", "youcam_task_id"):
            if key in data:
                sets.append(f"{key} = ?")
                params.append(data[key])
        if not sets:
            return None
        params.append(vton_id)
        await self.db.prepare(
            f"UPDATE vton_results SET {', '.join(sets)} WHERE id = ?"
        ).bind(*params).run()
        return await self.get_vton_result(vton_id)

    async def get_pending_vton_tasks(self, limit: int = 10) -> list[VtonResultModel]:
        """Get VTON results with status 'processing' that have a YouCam task ID."""
        d1_result = await self.db.prepare(
            "SELECT * FROM vton_results WHERE status = 'processing' AND youcam_task_id IS NOT NULL ORDER BY created_at ASC LIMIT ?"
        ).bind(limit).all()
        rows = d1_result.get("results", []) if isinstance(d1_result, dict) else d1_result
        return [VtonResultModel(row) for row in rows]

    # ── Favorites ──────────────────────────────────────────────

    async def add_favorite(self, user_id: str, product_id: str) -> None:
        """Add a product to user's favorites. Ignores duplicate."""
        import sqlite3
        try:
            await self.db.prepare(
                "INSERT OR IGNORE INTO favorites (id, user_id, product_id) VALUES (?, ?, ?)"
            ).bind(str(uuid.uuid4()), user_id, product_id).run()
        except Exception:
            pass

    async def remove_favorite(self, user_id: str, product_id: str) -> None:
        """Remove a product from user's favorites."""
        await self.db.prepare(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?"
        ).bind(user_id, product_id).run()

    async def is_favorite(self, user_id: str, product_id: str) -> bool:
        """Check if a product is in user's favorites."""
        result = await self.db.prepare(
            "SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ? LIMIT 1"
        ).bind(user_id, product_id).first()
        return result is not None

    async def get_favorites(self, user_id: str, page: int = 1, limit: int = 20):
        """Get user's favorite products with pagination."""
        count_result = await self.db.prepare(
            "SELECT COUNT(*) as total FROM favorites WHERE user_id = ?"
        ).bind(user_id).first()
        total = count_result["total"] if count_result else 0

        offset = (page - 1) * limit
        d1_result = await self.db.prepare(
            """SELECT p.* FROM products p
               INNER JOIN favorites f ON f.product_id = p.id
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC LIMIT ? OFFSET ?"""
        ).bind(user_id, limit, offset).all()

        rows = d1_result.get("results", []) if isinstance(d1_result, dict) else d1_result
        products = [ProductModel(row) for row in rows]
        return products, total

    async def get_vton_by_task_id(self, youcam_task_id: str) -> Optional[VtonResultModel]:
        """Get VTON result by YouCam task ID (used by webhook)."""
        result = await self.db.prepare(
            "SELECT * FROM vton_results WHERE youcam_task_id = ? LIMIT 1"
        ).bind(youcam_task_id).first()
        if result:
            return VtonResultModel(result)
        return None

    async def delete_vton_result(self, vton_id: str, user_id: str) -> bool:
        """Delete a VTON result record (with ownership check)."""
        await self.db.prepare(
            "DELETE FROM vton_results WHERE id = ? AND user_id = ?"
        ).bind(vton_id, user_id).run()
        return True
