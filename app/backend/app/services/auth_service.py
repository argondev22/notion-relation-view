"""
Auth Service for user authentication, session management, and token encryption.
"""
from datetime import datetime, timedelta
from typing import Optional
import base64
import os
import bcrypt
from jose import JWTError, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.notion_token import NotionToken




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

        Note: bcrypt has a maximum password length of 72 bytes.
        Passwords longer than this are truncated.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        # Truncate password to 72 bytes (bcrypt limitation)
        password_bytes = password.encode('utf-8')[:72]
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Note: bcrypt has a maximum password length of 72 bytes.
        Passwords longer than this are truncated before verification.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        # Truncate password to 72 bytes (bcrypt limitation)
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

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
            user_id: User ID (string or UUID)
            token: Plain text Notion API token
        """
        import uuid as uuid_lib

        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = uuid_lib.UUID(user_id)

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
            user_id: User ID (string or UUID)

        Returns:
            Plain text Notion API token, or None if not found
        """
        import uuid as uuid_lib

        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = uuid_lib.UUID(user_id)

        notion_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if not notion_token:
            return None

        return self.decrypt_notion_token(notion_token.encrypted_token)


# Create a singleton instance
auth_service = AuthService()
