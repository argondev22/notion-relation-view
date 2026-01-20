"""
Tests for Auth Service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt

from app.database import Base
from app.models.user import User
from app.models.notion_token import NotionToken
from app.services.auth_service import AuthService, auth_service
from app.config import settings


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    # Only create tables for User and NotionToken (not View which has ARRAY type)
    User.__table__.create(engine, checkfirst=True)
    NotionToken.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def auth_svc():
    """Create an AuthService instance for testing"""
    return AuthService()


class TestPasswordHashing:
    """Tests for password hashing functionality"""

    def test_hash_password(self, auth_svc):
        """Test that password hashing works"""
        password = "test_password_123"
        hashed = auth_svc.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self, auth_svc):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = auth_svc.hash_password(password)

        assert auth_svc.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_svc):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = auth_svc.hash_password(password)

        assert auth_svc.verify_password(wrong_password, hashed) is False

    def test_hash_password_different_salts(self, auth_svc):
        """Test that same password produces different hashes (due to salt)"""
        password = "test_password_123"
        hash1 = auth_svc.hash_password(password)
        hash2 = auth_svc.hash_password(password)

        assert hash1 != hash2


class TestUserRegistration:
    """Tests for user registration functionality"""

    def test_register_new_user(self, auth_svc, db_session):
        """Test registering a new user"""
        email = "test@example.com"
        password = "test_password_123"

        user = auth_svc.register(db_session, email, password)

        assert user is not None
        assert user.id is not None
        assert user.email == email
        assert user.password_hash != password
        assert user.created_at is not None

    def test_register_duplicate_email(self, auth_svc, db_session):
        """Test that registering with duplicate email raises error"""
        email = "test@example.com"
        password = "test_password_123"

        # Register first user
        auth_svc.register(db_session, email, password)

        # Try to register with same email
        with pytest.raises(ValueError, match="already exists"):
            auth_svc.register(db_session, email, password)

    def test_register_password_is_hashed(self, auth_svc, db_session):
        """Test that registered user's password is properly hashed"""
        email = "test@example.com"
        password = "test_password_123"

        user = auth_svc.register(db_session, email, password)

        # Password should be hashed, not plain text
        assert user.password_hash != password
        # Should be able to verify with original password
        assert auth_svc.verify_password(password, user.password_hash)


class TestUserLogin:
    """Tests for user login functionality"""

    def test_login_success(self, auth_svc, db_session):
        """Test successful login"""
        email = "test@example.com"
        password = "test_password_123"

        # Register user
        auth_svc.register(db_session, email, password)

        # Login
        result = auth_svc.login(db_session, email, password)

        assert result is not None
        assert "token" in result
        assert "expires_at" in result
        assert isinstance(result["token"], str)
        assert isinstance(result["expires_at"], datetime)

    def test_login_invalid_email(self, auth_svc, db_session):
        """Test login with non-existent email"""
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_svc.login(db_session, "nonexistent@example.com", "password")

    def test_login_invalid_password(self, auth_svc, db_session):
        """Test login with incorrect password"""
        email = "test@example.com"
        password = "test_password_123"
        wrong_password = "wrong_password"

        # Register user
        auth_svc.register(db_session, email, password)

        # Try to login with wrong password
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_svc.login(db_session, email, wrong_password)

    def test_login_token_contains_user_info(self, auth_svc, db_session):
        """Test that login token contains user information"""
        email = "test@example.com"
        password = "test_password_123"

        # Register user
        user = auth_svc.register(db_session, email, password)

        # Login
        result = auth_svc.login(db_session, email, password)

        # Decode token to verify contents
        payload = jwt.decode(
            result["token"],
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == str(user.id)
        assert payload["email"] == email
        assert "exp" in payload


class TestSessionValidation:
    """Tests for session validation functionality"""

    def test_validate_session_valid_token(self, auth_svc, db_session):
        """Test validating a valid session token"""
        email = "test@example.com"
        password = "test_password_123"

        # Register and login
        user = auth_svc.register(db_session, email, password)
        login_result = auth_svc.login(db_session, email, password)

        # Validate session
        session_info = auth_svc.validate_session(login_result["token"])

        assert session_info is not None
        assert session_info["user_id"] == str(user.id)
        assert session_info["email"] == email

    def test_validate_session_invalid_token(self, auth_svc):
        """Test validating an invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(ValueError, match="Invalid or expired token"):
            auth_svc.validate_session(invalid_token)

    def test_validate_session_expired_token(self, auth_svc):
        """Test validating an expired token"""
        # Create an expired token
        expired_time = datetime.utcnow() - timedelta(minutes=1)
        payload = {
            "sub": "user_id",
            "email": "test@example.com",
            "exp": expired_time
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(ValueError, match="Invalid or expired token"):
            auth_svc.validate_session(expired_token)

    def test_validate_session_missing_payload(self, auth_svc):
        """Test validating a token with missing payload fields"""
        # Create token without required fields
        payload = {"exp": datetime.utcnow() + timedelta(minutes=10)}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(ValueError, match="Invalid token payload"):
            auth_svc.validate_session(token)


class TestLogout:
    """Tests for logout functionality"""

    def test_logout_valid_token(self, auth_svc, db_session):
        """Test logout with valid token"""
        email = "test@example.com"
        password = "test_password_123"

        # Register and login
        auth_svc.register(db_session, email, password)
        login_result = auth_svc.login(db_session, email, password)

        # Logout should not raise error
        auth_svc.logout(login_result["token"])

    def test_logout_invalid_token(self, auth_svc):
        """Test logout with invalid token"""
        # Should not raise error even with invalid token
        auth_svc.logout("invalid.token.here")


class TestNotionTokenEncryption:
    """Tests for Notion token encryption/decryption"""

    def test_encrypt_notion_token(self, auth_svc):
        """Test encrypting a Notion token"""
        token = "secret_notion_token_123"
        encrypted = auth_svc.encrypt_notion_token(token)

        assert encrypted is not None
        assert encrypted != token
        assert len(encrypted) > 0

    def test_decrypt_notion_token(self, auth_svc):
        """Test decrypting a Notion token"""
        token = "secret_notion_token_123"
        encrypted = auth_svc.encrypt_notion_token(token)
        decrypted = auth_svc.decrypt_notion_token(encrypted)

        assert decrypted == token

    def test_encrypt_decrypt_roundtrip(self, auth_svc):
        """Test that encryption and decryption are inverse operations"""
        tokens = [
            "secret_notion_token_123",
            "another_token_456",
            "token_with_special_chars_!@#$%",
            "very_long_token_" + "x" * 100
        ]

        for token in tokens:
            encrypted = auth_svc.encrypt_notion_token(token)
            decrypted = auth_svc.decrypt_notion_token(encrypted)
            assert decrypted == token

    def test_decrypt_invalid_token(self, auth_svc):
        """Test decrypting an invalid encrypted token"""
        invalid_encrypted = "invalid_encrypted_token"

        with pytest.raises(ValueError, match="Failed to decrypt token"):
            auth_svc.decrypt_notion_token(invalid_encrypted)

    def test_encrypt_produces_different_ciphertexts(self, auth_svc):
        """Test that encrypting same token produces different ciphertexts (due to random nonce)"""
        token = "secret_notion_token_123"
        encrypted1 = auth_svc.encrypt_notion_token(token)
        encrypted2 = auth_svc.encrypt_notion_token(token)

        # Different ciphertexts due to random nonce
        assert encrypted1 != encrypted2

        # But both decrypt to same plaintext
        assert auth_svc.decrypt_notion_token(encrypted1) == token
        assert auth_svc.decrypt_notion_token(encrypted2) == token


class TestSaveNotionToken:
    """Tests for saving Notion tokens"""

    def test_save_notion_token_new(self, auth_svc, db_session):
        """Test saving a new Notion token"""
        # Create user
        user = auth_svc.register(db_session, "test@example.com", "password")

        # Save token
        token = "secret_notion_token_123"
        auth_svc.save_notion_token(db_session, str(user.id), token)

        # Verify token was saved
        saved_token = db_session.query(NotionToken).filter_by(user_id=user.id).first()
        assert saved_token is not None
        assert saved_token.encrypted_token is not None

    def test_save_notion_token_update_existing(self, auth_svc, db_session):
        """Test updating an existing Notion token"""
        # Create user
        user = auth_svc.register(db_session, "test@example.com", "password")

        # Save first token
        token1 = "secret_notion_token_123"
        auth_svc.save_notion_token(db_session, str(user.id), token1)

        # Save second token (should update)
        token2 = "new_secret_token_456"
        auth_svc.save_notion_token(db_session, str(user.id), token2)

        # Verify only one token exists and it's the new one
        tokens = db_session.query(NotionToken).filter_by(user_id=user.id).all()
        assert len(tokens) == 1

        # Decrypt and verify it's the new token
        decrypted = auth_svc.decrypt_notion_token(tokens[0].encrypted_token)
        assert decrypted == token2


class TestGetNotionToken:
    """Tests for retrieving Notion tokens"""

    def test_get_notion_token_exists(self, auth_svc, db_session):
        """Test retrieving an existing Notion token"""
        # Create user and save token
        user = auth_svc.register(db_session, "test@example.com", "password")
        token = "secret_notion_token_123"
        auth_svc.save_notion_token(db_session, str(user.id), token)

        # Retrieve token
        retrieved_token = auth_svc.get_notion_token(db_session, str(user.id))

        assert retrieved_token == token

    def test_get_notion_token_not_exists(self, auth_svc, db_session):
        """Test retrieving a non-existent Notion token"""
        # Create user without token
        user = auth_svc.register(db_session, "test@example.com", "password")

        # Try to retrieve token
        retrieved_token = auth_svc.get_notion_token(db_session, str(user.id))

        assert retrieved_token is None

    def test_save_and_get_notion_token_roundtrip(self, auth_svc, db_session):
        """Test that saving and retrieving a token returns the original value"""
        # Create user
        user = auth_svc.register(db_session, "test@example.com", "password")

        # Test multiple tokens
        tokens = [
            "secret_notion_token_123",
            "another_token_456",
            "token_with_special_chars_!@#$%"
        ]

        for token in tokens:
            auth_svc.save_notion_token(db_session, str(user.id), token)
            retrieved = auth_svc.get_notion_token(db_session, str(user.id))
            assert retrieved == token


class TestAuthServiceSingleton:
    """Tests for auth_service singleton"""

    def test_singleton_instance_exists(self):
        """Test that auth_service singleton is available"""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)
