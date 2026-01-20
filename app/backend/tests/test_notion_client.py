"""
Tests for Notion API Client
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.notion_client import (
    NotionAPIClient,
    InvalidTokenError,
    NetworkError,
    RateLimitError,
    PermissionError,
    NotionAPIError,
    notion_client
)


@pytest.fixture
def client():
    """Create a NotionAPIClient instance for testing"""
    return NotionAPIClient()


@pytest.fixture
def mock_token():
    """Mock Notion API token"""
    return "secret_test_token_123"


class TestAuthenticate:
    """Tests for authenticate method"""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, client, mock_token):
        """Test successful authentication"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "user",
            "id": "test-user-id",
            "name": "Test Workspace"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await client.authenticate(mock_token)

            assert result["success"] is True
            assert result["workspace_name"] == "Test Workspace"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, client):
        """Test authentication with invalid token"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": "unauthorized",
            "message": "Invalid token"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(InvalidTokenError, match="Invalid Notion API token"):
                await client.authenticate("invalid_token")

    @pytest.mark.asyncio
    async def test_authenticate_network_error(self, client, mock_token):
        """Test authentication with network error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
            mock_client_class.return_value = mock_client

            with pytest.raises(NetworkError, match="Network error"):
                await client.authenticate(mock_token)

    @pytest.mark.asyncio
    async def test_authenticate_timeout(self, client, mock_token):
        """Test authentication with timeout"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client_class.return_value = mock_client

            with pytest.raises(NetworkError, match="Request timeout"):
                await client.authenticate(mock_token)


class TestGetDatabases:
    """Tests for get_databases method"""

    @pytest.mark.asyncio
    async def test_get_databases_success(self, client, mock_token):
        """Test successful database retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "db1",
                    "title": [{"plain_text": "Database 1"}]
                },
                {
                    "id": "db2",
                    "title": [{"plain_text": "Database 2"}]
                }
            ],
            "has_more": False
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            databases = await client.get_databases(mock_token)

            assert len(databases) == 2
            assert databases[0]["id"] == "db1"
            assert databases[0]["title"] == "Database 1"
            assert databases[1]["id"] == "db2"
            assert databases[1]["title"] == "Database 2"

    @pytest.mark.asyncio
    async def test_get_databases_empty(self, client, mock_token):
        """Test database retrieval with no databases"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "has_more": False
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            databases = await client.get_databases(mock_token)

            assert len(databases) == 0

    @pytest.mark.asyncio
    async def test_get_databases_rate_limit(self, client, mock_token):
        """Test database retrieval with rate limit error"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {
            "code": "rate_limited",
            "message": "Rate limit exceeded"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(RateLimitError) as exc_info:
                await client.get_databases(mock_token)

            assert exc_info.value.retry_after == 60


class TestGetPages:
    """Tests for get_pages method"""

    @pytest.mark.asyncio
    async def test_get_pages_success(self, client, mock_token):
        """Test successful page retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "page1",
                    "properties": {
                        "Name": {
                            "type": "title",
                            "title": [{"plain_text": "Page 1"}]
                        }
                    }
                }
            ],
            "has_more": False
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            pages = await client.get_pages(mock_token, "db1")

            assert len(pages) == 1
            assert pages[0]["id"] == "page1"
            assert pages[0]["title"] == "Page 1"
            assert pages[0]["database_id"] == "db1"

    @pytest.mark.asyncio
    async def test_get_pages_empty_database(self, client, mock_token):
        """Test page retrieval from empty database"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "has_more": False
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            pages = await client.get_pages(mock_token, "empty_db")

            assert len(pages) == 0

    @pytest.mark.asyncio
    async def test_get_pages_permission_error(self, client, mock_token):
        """Test page retrieval with permission error"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "code": "restricted_resource",
            "message": "Permission denied"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(PermissionError, match="Permission denied"):
                await client.get_pages(mock_token, "restricted_db")


class TestExtractRelations:
    """Tests for extract_relations method"""

    def test_extract_relations_with_relations(self, client):
        """Test extracting relations from a page with relation properties"""
        page = {
            "id": "page1",
            "properties": {
                "Related Pages": {
                    "type": "relation",
                    "relation": [
                        {"id": "page2"},
                        {"id": "page3"}
                    ]
                }
            }
        }

        relations = client.extract_relations(page)

        assert len(relations) == 2
        assert relations[0]["source_page_id"] == "page1"
        assert relations[0]["target_page_id"] == "page2"
        assert relations[0]["property_name"] == "Related Pages"

    def test_extract_relations_no_relations(self, client):
        """Test extracting relations from a page without relation properties"""
        page = {
            "id": "page1",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Page 1"}]
                }
            }
        }

        relations = client.extract_relations(page)

        assert len(relations) == 0


class TestFetchPagesInBatch:
    """Tests for fetch_pages_in_batch method"""

    @pytest.mark.asyncio
    async def test_fetch_pages_in_batch_success(self, client, mock_token):
        """Test successful batch page retrieval"""
        page_ids = ["page1", "page2"]

        def create_response(page_id):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "id": page_id,
                "properties": {
                    "Name": {"type": "title", "title": [{"plain_text": f"Page {page_id[-1]}"}]}
                },
                "parent": {"database_id": "db1"}
            }
            return resp

        mock_responses = [create_response("page1"), create_response("page2")]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=mock_responses)
            mock_client_class.return_value = mock_client

            pages = await client.fetch_pages_in_batch(mock_token, page_ids)

            assert len(pages) == 2
            assert pages[0]["id"] == "page1"

    @pytest.mark.asyncio
    async def test_fetch_pages_in_batch_empty_list(self, client, mock_token):
        """Test batch page retrieval with empty page list"""
        pages = await client.fetch_pages_in_batch(mock_token, [])

        assert len(pages) == 0


class TestNotionClientSingleton:
    """Tests for notion_client singleton"""

    def test_singleton_instance_exists(self):
        """Test that notion_client singleton is available"""
        assert notion_client is not None
        assert isinstance(notion_client, NotionAPIClient)
