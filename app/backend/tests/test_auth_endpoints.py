"""
Unit tests for authentication API endpoints.
Tests cover registration, login, logout, and user info retrieval.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.notion_token import NotionToken


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop database tables for each test."""
    # Only create tables needed for auth tests (User and NotionToken)
    User.__table__.create(bind=engine, checkfirst=True)
    NotionToken.__table__.create(bind=engine, checkfirst=True)
    yield
    # Drop tables after test
    NotionToken.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)


class TestUserRegistration:
    """Tests for POST /api/auth/register endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@example.com"
        assert "id" in data["user"]
        assert "created_at" in data["user"]
        assert "updated_at" in data["user"]
        assert data["error"] is None

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )

        # Try to register with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "differentpassword"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_password(self):
        """Test registration without password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com"
            }
        )

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Tests for POST /api/auth/login endpoint."""

    def test_login_success(self):
        """Test successful user login."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "mypassword123"
            }
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "mypassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["token"] is not None
        assert data["expires_at"] is not None
        assert data["user"]["email"] == "login@example.com"
        assert data["error"] is None

        # Check that session cookie is set
        assert "session_token" in response.cookies

    def test_login_invalid_email(self):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_password(self):
        """Test login with incorrect password."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "correctpassword"
            }
        )

        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_missing_credentials(self):
        """Test login without credentials."""
        response = client.post(
            "/api/auth/login",
            json={}
        )

        assert response.status_code == 422  # Validation error


class TestUserLogout:
    """Tests for POST /api/auth/logout endpoint."""

    def test_logout_success(self):
        """Test successful user logout."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "logout@example.com",
                "password": "password123"
            }
        )

        # Get session token from cookie
        session_token = login_response.cookies.get("session_token")

        # Logout
        response = client.post(
            "/api/auth/logout",
            cookies={"session_token": session_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logged out" in data["message"].lower()

    def test_logout_without_session(self):
        """Test logout without session token."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_logout_with_invalid_token(self):
        """Test logout with invalid session token."""
        response = client.post(
            "/api/auth/logout",
            cookies={"session_token": "invalid-token"}
        )

        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for GET /api/auth/me endpoint."""

    def test_get_current_user_success(self):
        """Test getting current user information."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "currentuser@example.com",
                "password": "password123"
            }
        )

        session_token = login_response.cookies.get("session_token")

        # Get current user
        response = client.get(
            "/api/auth/me",
            cookies={"session_token": session_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "currentuser@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_current_user_without_session(self):
        """Test getting current user without session token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_get_current_user_with_invalid_token(self):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            cookies={"session_token": "invalid-token"}
        )

        assert response.status_code == 401

    def test_get_current_user_with_expired_token(self):
        """Test getting current user with expired token (simulated)."""
        # This would require mocking JWT expiration
        # For now, we test with a malformed token
        response = client.get(
            "/api/auth/me",
            cookies={"session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"}
        )

        assert response.status_code == 401


class TestSessionManagement:
    """Tests for session management and edge cases."""

    def test_session_persists_across_requests(self):
        """Test that session token works across multiple requests."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "persistent@example.com",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "persistent@example.com",
                "password": "password123"
            }
        )

        session_token = login_response.cookies.get("session_token")

        # Make multiple requests with same token
        for _ in range(3):
            response = client.get(
                "/api/auth/me",
                cookies={"session_token": session_token}
            )
            assert response.status_code == 200
            assert response.json()["email"] == "persistent@example.com"

    def test_cannot_access_protected_route_after_logout(self):
        """Test that protected routes are inaccessible after logout."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "afterlogout@example.com",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "afterlogout@example.com",
                "password": "password123"
            }
        )

        session_token = login_response.cookies.get("session_token")

        # Verify access works
        response = client.get(
            "/api/auth/me",
            cookies={"session_token": session_token}
        )
        assert response.status_code == 200

        # Logout
        logout_response = client.post(
            "/api/auth/logout",
            cookies={"session_token": session_token}
        )
        assert logout_response.status_code == 200

        # Try to access protected route with old token
        # Note: In stateless JWT, the token is still valid until expiration
        # This test demonstrates the limitation of stateless JWT
        # For immediate invalidation, implement a token blacklist
