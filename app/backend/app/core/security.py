"""
Security utilities for JWT and encryption
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
from app.core.config import settings


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for user authentication

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    payload = {"sub": user_id, "exp": expire, "iat": now, "type": "access"}

    encoded_jwt = jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


# JWTトークンを検証してペイロードを返す
def verify_token(token: str) -> dict:
    pass


# Notion APIトークンをAES-256-GCMで暗号化
def encrypt_notion_token(token: str) -> str:
    pass


# 暗号化されたトークンを復号化
def decrypt_notion_token(encrypted_token: str) -> str:
    pass
