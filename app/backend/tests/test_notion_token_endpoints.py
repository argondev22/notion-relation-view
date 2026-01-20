"""
Unit tests for Notion token API endpoints.

Tests cover:
- Token saving with encryption
- Token verification
- Invalid token error handling
- Token encryption validation
"""
import pytest
from unittest.mock import patch
from .conftest import client, TestingSessionLocal
from app.services.auth_service import auth_service
from app.models.notion_token import NotionToken


@pytest.fixture
def test_user():
    """Create a test user and return user with session token"""
    db = TestingSessionLocal()

    # Register user
    user = auth_service.register(db, "test@example.com", "password123")

    # Login to get session token
    session_data = auth_service.login(db, "test@example.com", "password123")

    db.close()

    return {
        "user": user,
        "token": session_data["token"]
    }


class TestSaveNotionToken:
    """Tests for POST /api/notion/token endpoint"""

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_save_valid_token(self, mock_authenticate, client, test_user):
        """
        Test saving a valid Notion token.

        Validates: Requirements 1.1, 6.1
        """
        # Mock successful authentication
        mock_authenticate.return_value = {
            "success": True,
            "workspace_name": "Test Workspace"
        }

        # Make request with valid token
        response = client.post(
            "/api/notion/token",
            json={"token": "secret_test_token_12345"},
            cookies={"session_token": test_user["token"]}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Notion token saved successfully"
        assert data["workspace_name"] == "Test Workspace"

        # Verify token was encrypted and saved
        db = TestingSessionLocal()
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == test_user["user"].id
        ).first()
        assert stored_token is not None
        assert stored_token.encrypted_token != "secret_test_token_12345"

        # Verify token can be decrypted
        decrypted = auth_service.decrypt_notion_token(stored_token.encrypted_token)
        assert decrypted == "secret_test_token_12345"
        db.close()

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_save_invalid_token(self, mock_authenticate, client, test_user):
        """
        Test saving an invalid Notion token.

        Validates: Requirements 1.3, 6.1
        """
        # Mock authentication failure
        from app.services.notion_client import InvalidTokenError
        mock_authenticate.side_effect = InvalidTokenError("Invalid token")

        # Make request with invalid token
        response = client.post(
            "/api/notion/token",
            json={"token": "invalid_token"},
            cookies={"session_token": test_user["token"]}
        )

        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid Notion API token" in data["detail"]

        # Verify token was not saved
        db = TestingSessionLocal()
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == test_user["user"].id
        ).first()
        assert stored_token is None
        db.close()

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_update_existing_token(self, mock_authenticate, client, test_user):
        """
        Test updating an existing Notion token.

        Validates: Requirements 6.1
        """
        # Mock successful authentication
        mock_authenticate.return_value = {
            "success": True,
            "workspace_name": "Test Workspace"
        }

        # Save first token
        response1 = client.post(
            "/api/notion/token",
            json={"token": "secret_token_1"},
            cookies={"session_token": test_user["token"]}
        )
        assert response1.status_code == 200

        # Save second token (should update)
        response2 = client.post(
            "/api/notion/token",
            json={"token": "secret_token_2"},
            cookies={"session_token": test_user["token"]}
        )
        assert response2.status_code == 200

        # Verify only one token exists and it's the new one
        db = TestingSessionLocal()
        tokens = db.query(NotionToken).filter(
            NotionToken.user_id == test_user["user"].id
        ).all()
        assert len(tokens) == 1

        decrypted = auth_service.decrypt_notion_token(tokens[0].encrypted_token)
        assert decrypted == "secret_token_2"
        db.close()

    def test_save_token_without_authentication(self, client):
        """
        Test saving token without being authenticated.

        Validates: Requirements 6.1
        """
        response = client.post(
            "/api/notion/token",
            json={"token": "secret_test_token"}
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_save_token_network_error(self, mock_authenticate, client, test_user):
        """
        Test handling network errors during token verification.

        Validates: Requirements 1.3
        """
        # Mock network error
        from app.services.notion_client import NetworkError
        mock_authenticate.side_effect = NetworkError("Connection failed")

        response = client.post(
            "/api/notion/token",
            json={"token": "secret_test_token"},
            cookies={"session_token": test_user["token"]}
        )

        # Should return 503 Service Unavailable
        assert response.status_code == 503
        assert "Network error" in response.json()["detail"]


class TestVerifyNotionToken:
    """Tests for GET /api/notion/token/verify endpoint"""

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_verify_valid_token(self, mock_authenticate, client, test_user):
        """
        Test verifying a valid stored Notion token.

        Validates: Requirements 1.1, 1.3
        """
        # First, save a token
        db = TestingSessionLocal()
        encrypted_token = auth_service.encrypt_notion_token("secret_valid_token")
        notion_token = NotionToken(
            user_id=test_user["user"].id,
            encrypted_token=encrypted_token
        )
        db.add(notion_token)
        db.commit()
        db.close()

        # Mock successful verification
        mock_authenticate.return_value = {
            "success": True,
            "workspace_name": "Test Workspace"
        }

        # Verify token
        response = client.get(
            "/api/notion/token/verify",
            cookies={"session_token": test_user["token"]}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["workspace_name"] == "Test Workspace"
        assert data["error"] is None

    def test_verify_no_token_stored(self, client, test_user):
        """
        Test verifying when no token is stored.

        Validates: Requirements 1.3
        """
        response = client.get(
            "/api/notion/token/verify",
            cookies={"session_token": test_user["token"]}
        )

        # Should return valid=False with error message
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "No Notion token stored" in data["error"]

    @patch("app.services.notion_client.notion_client.authenticate")
    def test_verify_invalid_token(self, mock_authenticate, client, test_user):
        """
        Test verifying an invalid stored token.

        Validates: Requirements 1.3
        """
        # Save a token
        db = TestingSessionLocal()
        encrypted_token = auth_service.encrypt_notion_token("secret_invalid_token")
        notion_token = NotionToken(
            user_id=test_user["user"].id,
            encrypted_token=encrypted_token
        )
        db.add(notion_token)
        db.commit()
        db.close()

        # Mock authentication failure
        from app.services.notion_client import InvalidTokenError
        mock_authenticate.side_effect = InvalidTokenError("Invalid token")

        # Verify token
        response = client.get(
            "/api/notion/token/verify",
            cookies={"session_token": test_user["token"]}
        )

        # Should return valid=False
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Invalid Notion API token" in data["error"]

    def test_verify_without_authentication(self, client):
        """
        Test verifying token without being authenticated.

        Validates: Requirements 6.1
        """
        response = client.get("/api/notion/token/verify")

        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestTokenEncryption:
    """Tests for token encryption validation"""

    def test_token_encryption_roundtrip(self):
        """
        Test that token encryption and decryption work correctly.

        Validates: Requirements 6.1
        """
        original_token = "secret_test_token_12345"

        # Encrypt
        encrypted = auth_service.encrypt_notion_token(original_token)

        # Verify encrypted is different from original
        assert encrypted != original_token

        # Decrypt
        decrypted = auth_service.decrypt_notion_token(encrypted)

        # Verify decrypted matches original
        assert decrypted == original_token

    def test_token_encryption_produces_different_ciphertexts(self):
        """
        Test that encrypting the same token twice produces different ciphertexts.

        This is important for security (nonce randomness).

        Validates: Requirements 6.1
        """
        token = "secret_test_token"

        encrypted1 = auth_service.encrypt_notion_token(token)
        encrypted2 = auth_service.encrypt_notion_token(token)

        # Should be different due to random nonce
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert auth_service.decrypt_notion_token(encrypted1) == token
        assert auth_service.decrypt_notion_token(encrypted2) == token

    def test_invalid_encrypted_token_raises_error(self):
        """
        Test that decrypting an invalid token raises an error.

        Validates: Requirements 6.1
        """
        with pytest.raises(ValueError):
            auth_service.decrypt_notion_token("invalid_encrypted_data")
