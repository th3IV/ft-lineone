"""Authentication service for JWT tokens."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    email: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_jwt_secret() -> str:
    """Get JWT secret from environment."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Generate a secure random secret for development
        secret = secrets.token_urlsafe(64)
        os.environ["JWT_SECRET"] = secret
    return secret


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    return jwt.encode(to_encode, get_jwt_secret(), algorithm=os.getenv("JWT_ALGORITHM", "HS256"))


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=30)

    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    return jwt.encode(to_encode, get_jwt_secret(), algorithm=os.getenv("JWT_ALGORITHM", "HS256"))


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id and email:
            return TokenData(user_id=user_id, email=email)
    except jwt.PyJWTError:
        pass
    return None


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
