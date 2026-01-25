"""
Unit tests for Graph API endpoints.

Tests cover:
- Graph data retrieval
- Database list retrieval
- Empty database handling
- Pages without relations (isolated nodes)
- Error handling
"""
import pytest
from unittest.mock import patch, AsyncMock
from .conftest import client, TestingSessionLocal
from app.services.auth_service import auth_service
from app.models.notion_token import NotionToken


@pytest.fixture
def test_user_with_token():
    """Create a test user with a Notion token"""
    db = TestingSessionLocal()

    # Register user
    user = auth_service.register(db, "test@example.com", "password123")

    # Login to get session token
    session_data = auth_service.login(db, "test@example.com", "password123")

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


class TestGetGraphData:
    """Tests for GET /api/graph/data endpoint"""

    def test_get_graph_data_success(self, client, test_user_with_token):
        """
        Test successful graph data retrieval.

        Validates: Requirements 2.1, 2.4, 3.1, 3.2, 3.3
        """
        with patch("app.services.notion_client.notion_client.get_databases", new_callable=AsyncMock) as mock_get_databases, \
             patch("app.services.notion_client.notion_client.get_pages", new_callable=AsyncMock) as mock_get_pages:

            # Mock database response
            mock_get_databases.return_value = [
                {"id": "db-1", "title": "Database 1"}
            ]

            # Mock pages response
            mock_get_pages.return_value = [
                {
                    "id": "page-1",
                    "title": "Page 1",
                    "database_id": "db-1",
                    "properties": {
                        "Title": {"type": "title", "title": [{"plain_text": "Page 1"}]},
                        "Related": {"type": "relation", "relation": [{"id": "page-2"}]}
                    }
                },
                {
                    "id": "page-2",
                    "title": "Page 2",
                    "database_id": "db-1",
                    "properties": {
                        "Title": {"type": "title", "title": [{"plain_text": "Page 2"}]}
                    }
                }
            ]

            # Make request
            response = client.get(
                "/api/graph/data",
                cookies={"session_token": test_user_with_token["token"]}
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "nodes" in data
            assert "edges" in data
            assert "databases" in data

            # Verify nodes
            assert len(data["nodes"]) == 2

    def test_get_graph_data_empty_database(self, client, test_user_with_token):
        """
        Test graph data retrieval with empty database.

        Validates: Requirement 2.5 (empty database handling)
        """
        with patch("app.services.notion_client.notion_client.get_databases", new_callable=AsyncMock) as mock_get_databases, \
             patch("app.services.notion_client.notion_client.get_pages", new_callable=AsyncMock) as mock_get_pages:

            mock_get_databases.return_value = [{"id": "db-1", "title": "Empty Database"}]
            mock_get_pages.return_value = []

            response = client.get(
                "/api/graph/data",
                cookies={"session_token": test_user_with_token["token"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["nodes"]) == 0
            assert len(data["edges"]) == 0
            assert len(data["databases"]) == 1

    def test_get_graph_data_pages_without_relations(self, client, test_user_with_token):
        """
        Test graph data retrieval with pages that have no relations (isolated nodes).

        Validates: Requirement 2.5 (isolated node handling)
        """
        with patch("app.services.notion_client.notion_client.get_databases", new_callable=AsyncMock) as mock_get_databases, \
             patch("app.services.notion_client.notion_client.get_pages", new_callable=AsyncMock) as mock_get_pages:

            mock_get_databases.return_value = [{"id": "db-1", "title": "Database 1"}]
            mock_get_pages.return_value = [
                {
                    "id": "page-1",
                    "title": "Isolated Page 1",
                    "database_id": "db-1",
                    "properties": {
                        "Title": {"type": "title", "title": [{"plain_text": "Isolated Page 1"}]}
                    }
                }
            ]

            response = client.get(
                "/api/graph/data",
                cookies={"session_token": test_user_with_token["token"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["nodes"]) == 1
            assert len(data["edges"]) == 0

    def test_get_graph_data_no_token(self, client):
        """
        Test graph data retrieval without Notion token.

        Validates: Error handling when no token is stored
        """
        db = TestingSessionLocal()
        user = auth_service.register(db, "notoken@example.com", "password123")
        session_data = auth_service.login(db, "notoken@example.com", "password123")
        db.close()

        response = client.get(
            "/api/graph/data",
            cookies={"session_token": session_data["token"]}
        )

        assert response.status_code == 404
        data = response.json()
        assert "No Notion token" in data["detail"]

    def test_get_graph_data_unauthorized(self, client):
        """
        Test graph data retrieval without authentication.

        Validates: Authentication requirement
        """
        response = client.get("/api/graph/data")
        assert response.status_code == 401


class TestGetDatabases:
    """Tests for GET /api/graph/databases endpoint"""

    def test_get_databases_success(self, client, test_user_with_token):
        """
        Test successful database list retrieval.

        Validates: Requirements 2.1, 2.4
        """
        with patch("app.services.notion_client.notion_client.get_databases", new_callable=AsyncMock) as mock_get_databases:
            mock_get_databases.return_value = [
                {"id": "db-1", "title": "Database 1"},
                {"id": "db-2", "title": "Database 2"}
            ]

            response = client.get(
                "/api/graph/databases",
                cookies={"session_token": test_user_with_token["token"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_databases_empty(self, client, test_user_with_token):
        """
        Test database list retrieval with no databases.

        Validates: Empty database list handling
        """
        with patch("app.services.notion_client.notion_client.get_databases", new_callable=AsyncMock) as mock_get_databases:
            mock_get_databases.return_value = []

            response = client.get(
                "/api/graph/databases",
                cookies={"session_token": test_user_with_token["token"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
            assert isinstance(data, list)

    def test_get_databases_no_token(self, client):
        """
        Test database list retrieval without Notion token.

        Validates: Error handling when no token is stored
        """
        db = TestingSessionLocal()
        user = auth_service.register(db, "notoken2@example.com", "password123")
        session_data = auth_service.login(db, "notoken2@example.com", "password123")
        db.close()

        response = client.get(
            "/api/graph/databases",
            cookies={"session_token": session_data["token"]}
        )

        assert response.status_code == 404
        data = response.json()
        assert "No Notion token" in data["detail"]

    def test_get_databases_unauthorized(self, client):
        """
        Test database list retrieval without authentication.

        Validates: Authentication requirement
        """
        response = client.get("/api/graph/databases")
        assert response.status_code == 401
