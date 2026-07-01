"""Cloudflare D1 Database Service using SQLAlchemy."""

import os
from typing import Optional

from sqlalchemy import create_engine, text, Column, String, Float, Boolean, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()


# SQLAlchemy Models for D1
class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    body_measurements = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, nullable=False, index=True)
    store = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    price = Column(Float, nullable=False)
    currency = Column(String, default="CLP")
    original_url = Column(String, default="")
    image_url = Column(String, nullable=True)
    image_urls = Column(JSON, default=list)
    category = Column(String, default="", index=True)
    sizes = Column(JSON, default=list)
    colors = Column(JSON, default=list)
    availability = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VtonResultModel(Base):
    __tablename__ = "vton_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    status = Column(String, default="pending")
    input_image_url = Column(String, nullable=True)
    output_image_url = Column(String, nullable=True)
    garment_image_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class DatabaseService:
    """D1 Database service using SQLAlchemy."""

    def __init__(self, env):
        """Initialize with Cloudflare Workers env."""
        self.env = env
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        if self._engine is None:
            # In Cloudflare Workers, D1 is accessed via the binding
            # For local development, use a SQLite file
            database_url = os.getenv("DATABASE_URL", "sqlite:///./ft_lineone.db")
            self._engine = create_engine(database_url)
        return self._engine

    @property
    def session_factory(self):
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a database session."""
        return self.session_factory()

    async def execute_query(self, query: str, params: dict = None):
        """Execute a raw query (for D1 binding)."""
        if hasattr(self.env, 'DB'):
            # Cloudflare Workers D1 binding
            result = await self.env.DB.prepare(query).bind(*params.values()).all()
            return result
        else:
            # Local SQLite fallback
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                return result

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        with self.get_session() as session:
            return session.query(UserModel).filter(UserModel.email == email).first()

    async def create_user(self, user_data: dict) -> UserModel:
        """Create a new user."""
        with self.get_session() as session:
            user = UserModel(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    async def get_product(self, product_id: str) -> Optional[ProductModel]:
        """Get product by ID."""
        with self.get_session() as session:
            return session.query(ProductModel).filter(ProductModel.id == product_id).first()

    async def get_products(self, filters: dict, page: int = 1, limit: int = 20):
        """Get products with filters."""
        with self.get_session() as session:
            query = session.query(ProductModel)

            if filters.get("store"):
                query = query.filter(ProductModel.store == filters["store"])
            if filters.get("category"):
                query = query.filter(ProductModel.category == filters["category"])
            if filters.get("min_price"):
                query = query.filter(ProductModel.price >= filters["min_price"])
            if filters.get("max_price"):
                query = query.filter(ProductModel.price <= filters["max_price"])
            if filters.get("query"):
                query = query.filter(ProductModel.name.ilike(f"%{filters['query']}%"))

            total = query.count()
            products = query.offset((page - 1) * limit).limit(limit).all()
            return products, total

    async def create_product(self, product_data: dict) -> ProductModel:
        """Create a new product."""
        with self.get_session() as session:
            product = ProductModel(**product_data)
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
