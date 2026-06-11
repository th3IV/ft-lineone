import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    body_measurements = Column(JSON, default=dict)
    preferences = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), nullable=False, index=True)
    store = Column(String(100), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    image_url = Column(Text, default="")
    category = Column(String(255), default="")
    sizes = Column(ARRAY(String), default=list)
    colors = Column(ARRAY(String), default=list)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VTONResultModel(Base):
    __tablename__ = "vton_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    input_image_url = Column(Text, nullable=False)
    output_image_url = Column(Text, default="")
    status = Column(Enum("pending", "processing", "completed", "failed", name="vton_status"), default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
