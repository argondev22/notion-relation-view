"""
Security utilities for JWT and encryption
"""

from datetime import datetime, timedelta, timezone
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


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    return payload

def _get_encryption_key() -> bytes:
    """
    Derive encryption key from settings using PBKDF2

    Returns:
        32-byte encryption key suitable for Fernet
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"notion-relation-view-salt",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
    return key

def encrypt_notion_token(token: str) -> str:
    """
    Encrypt Notion API token using AES-256-GCM (via Fernet)

    Args:
        token: Plain text Notion API token

    Returns:
        Encrypted token as base64 string
    """
    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


# 暗号化されたトークンを復号化
def decrypt_notion_token(encrypted_token: str) -> str:
    """
    Decrypt Notion API token

    Args:
        encrypted_token: Encrypted token string with salt

    Returns:
        Decrypted plain text token
    """
    # base64デコード
    combined = base64.urlsafe_b64decode(encrypted_token.encode())

    # saltと暗号化データを分離
    salt = combined[:16]
    encrypted = combined[16:]

    key = _get_encryption_key(salt)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)
    return decrypted.decode()
