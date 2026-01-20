"""
Auth Service for user authentication, session management, and token encryption.
"""
from datetime import datetime, timedelta
from typing import Optional
import base64
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.notion_token import NotionToken


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication, session management, and encryption."""

    def __init__(self):
        """Initialize the auth service with encryption key."""
        # Derive a 256-bit key from the encryption key using PBKDF2
        self._encryption_key = self._derive_key(settings.ENCRYPTION_KEY)

    @staticmethod
    def _derive_key(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a 256-bit encryption key from a password using PBKDF2-HMAC-SHA256.

        Args:
            password: The password/key to derive from
            salt: Optional salt (if None, uses a fixed salt for deterministic key derivation)

        Returns:
            32-byte encryption key
        """
        if salt is None:
            # Use a fixed salt for deterministic key derivation
            # In production, this should be stored securely
            salt = b"notion-relation-view-salt-v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with salt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    def register(self, db: Session, email: str, password: str) -> User:
        """
        Register a new user with hashed password.

        Args:
            db: Database session
            email: User email address
            password: Plain text password

        Returns:
            Created User object

        Raises:
            ValueError: If user with email already exists
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Hash the password
        password_hash = self.hash_password(password)

        # Create new user
        user = User(
            email=email,
            password_hash=password_hash
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def login(self, db: Session, email: str, password: str) -> dict:
        """
        Authenticate user and generate JWT session token.

        Args:
            db: Database session
            email: User email address
            password: Plain text password

        Returns:
            Dictionary with 'token' and 'expires_at' keys

        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Generate JWT token
        expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expires_at
        }

        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return {
            "token": token,
            "expires_at": expires_at
        }

    def validate_session(self, token: str) -> dict:
        """
        Validate a JWT session token and extract user information.

        Args:
            token: JWT token string

        Returns:
            Dictionary with user information (user_id, email)

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            user_id = payload.get("sub")
            email = payload.get("email")

            if user_id is None or email is None:
                raise ValueError("Invalid token payload")

            return {
                "user_id": user_id,
                "email": email
            }

        except JWTError as e:
            raise ValueError(f"Invalid or expired token: {str(e)}")

    def logout(self, token: str) -> None:
        """
        Invalidate a session token (logout).

        Note: With JWT, we don't maintain server-side session state.
        The token will naturally expire. For immediate invalidation,
        a token blacklist could be implemented in the future.

        Args:
            token: JWT token to invalidate
        """
        # Validate the token to ensure it's well-formed
        try:
            self.validate_session(token)
        except ValueError:
            # Token is already invalid
            pass

        # In a stateless JWT implementation, we don't need to do anything
        # The client will discard the token
        # For enhanced security, implement a token blacklist in Redis

    def encrypt_notion_token(self, token: str) -> str:
        """
        Encrypt a Notion API token using AES-256-GCM.

        Args:
            token: Plain text Notion API token

        Returns:
            Base64-encoded encrypted token with nonce
        """
        # Generate a random 96-bit nonce
        nonce = os.urandom(12)

        # Create AESGCM cipher
        aesgcm = AESGCM(self._encryption_key)

        # Encrypt the token
        ciphertext = aesgcm.encrypt(nonce, token.encode(), None)

        # Combine nonce and ciphertext, then base64 encode
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode()

    def decrypt_notion_token(self, encrypted_token: str) -> str:
        """
        Decrypt a Notion API token using AES-256-GCM.

        Args:
            encrypted_token: Base64-encoded encrypted token

        Returns:
            Plain text Notion API token

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_token)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]

            # Create AESGCM cipher
            aesgcm = AESGCM(self._encryption_key)

            # Decrypt the token
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext.decode()

        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {str(e)}")

    def save_notion_token(self, db: Session, user_id: str, token: str) -> None:
        """
        Encrypt and save a Notion API token for a user.

        Args:
            db: Database session
            user_id: User ID
            token: Plain text Notion API token
        """
        encrypted_token = self.encrypt_notion_token(token)

        # Check if token already exists
        existing_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if existing_token:
            # Update existing token
            existing_token.encrypted_token = encrypted_token
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token
            notion_token = NotionToken(
                user_id=user_id,
                encrypted_token=encrypted_token
            )
            db.add(notion_token)

        db.commit()

    def get_notion_token(self, db: Session, user_id: str) -> Optional[str]:
        """
        Retrieve and decrypt a Notion API token for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Plain text Notion API token, or None if not found
        """
        notion_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if not notion_token:
            return None

        return self.decrypt_notion_token(notion_token.encrypted_token)


# Create a singleton instance
auth_service = AuthService()
