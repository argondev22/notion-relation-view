"""
Unit tests for View Management API endpoints.

Tests cover:
- View creation, retrieval, update, deletion
- Error handling for non-existent views
"""
import pytest
from .conftest import client, TestingSessionLocal
from app.services.auth_service import auth_service
from app.models.notion_token import NotionToken


@pytest.fixture
def test_user_with_token():
    """Create a test user with a Notion token"""
    db = TestingSessionLocal()

    # Register user
    user = auth_service.register(db, "viewuser@example.com", "password123")

    # Login to get session token
    session_data = auth_service.login(db, "viewuser@example.com", "password123")

    # Save encrypted Notion token
    encrypted_token = auth_service.encrypt_notion_token("secret_test_token_12345")
    notion_token = NotionToken(
        user_id=user.id,
        encrypted_token=encrypted_token
    )
    db.add(notion_token)
    db.commit()

    db.close()

    return {
        "user": user,
        "token": session_data["token"]
    }


class TestViewManagement:
    """Tests for view management endpoints"""

    def test_create_view_success(self, client, test_user_with_token):
        """
        Test successful view creation.

        Validates: Requirements 6.3, 6.4
        """
        response = client.post(
            "/api/views",
            json={
                "name": "My Test View",
                "database_ids": ["db-1", "db-2"],
                "zoom_level": 1.5,
                "pan_x": 100.0,
                "pan_y": -50.0
            },
            cookies={"session_token": test_user_with_token["token"]}
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == "My Test View"
        assert data["database_ids"] == ["db-1", "db-2"]
        assert data["zoom_level"] == 1.5

    def test_get_nonexistent_view(self, client, test_user_with_token):
        """
        Test retrieving a non-existent view.

        Validates: Requirement 6.9 (error handling)
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/views/{fake_id}",
            cookies={"session_token": test_user_with_token["token"]}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_delete_view_success(self, client, test_user_with_token):
        """
        Test successful view deletion.

        Validates: Requirement 6.9
        """
        # Create a view
        create_response = client.post(
            "/api/views",
            json={
                "name": "To Delete",
                "database_ids": ["db-1"]
            },
            cookies={"session_token": test_user_with_token["token"]}
        )

        view_id = create_response.json()["id"]

        # Delete the view
        response = client.delete(
            f"/api/views/{view_id}",
            cookies={"session_token": test_user_with_token["token"]}
        )

        assert response.status_code == 204

        # Verify view is deleted
        get_response = client.get(
            f"/api/views/{view_id}",
            cookies={"session_token": test_user_with_token["token"]}
        )

        assert get_response.status_code == 404

    def test_delete_nonexistent_view(self, client, test_user_with_token):
        """
        Test deleting a non-existent view.

        Validates: Requirement 6.9 (error handling)
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/api/views/{fake_id}",
            cookies={"session_token": test_user_with_token["token"]}
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
