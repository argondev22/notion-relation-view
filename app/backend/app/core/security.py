"""
Security utilities for JWT and encryption
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
from app.core.config import settings

SALT_LENGTH = 16  # bytes
KEY_LENGTH = 32  # bytes
KDF_ITERATIONS = 100_000


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


def verify_token(token: str) -> Dict[str, Any]:
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


def _get_encryption_key(salt: bytes) -> bytes:
    """
    Derive encryption key from settings using PBKDF2

    Args:
        salt: Random salt for key derivation

    Returns:
        32-byte encryption key suitable for Fernet
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
    return key


def encrypt_notion_token(token: str) -> str:
    """
    Encrypt Notion API token using AES-256-GCM (via Fernet)

    Args:
        token: Plain text Notion API token

    Returns:
        Encrypted token with salt as base64 string
    """
    if not token or not token.strip():
        raise ValueError("Token cannot be empty")

    salt = os.urandom(SALT_LENGTH)

    key = _get_encryption_key(salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(token.encode())

    combined = salt + encrypted
    return base64.urlsafe_b64encode(combined).decode()


def decrypt_notion_token(encrypted_token: str) -> str:
    """
    Decrypt Notion API token

    Args:
        encrypted_token: Encrypted token string with salt

    Returns:
        Decrypted plain text token
    """
    try:
        combined = base64.urlsafe_b64decode(encrypted_token.encode())

        if len(combined) < SALT_LENGTH:
            raise ValueError("Invalid encrypted token: too short")

        salt = combined[:SALT_LENGTH]
        encrypted = combined[SALT_LENGTH:]

        key = _get_encryption_key(salt)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt token: {str(e)}")
