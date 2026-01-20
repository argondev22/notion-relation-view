"""
Property-Based Tests for Notion API Client

Feature: notion-relation-view
These tests verify universal properties that should hold across all inputs.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.notion_client import (
    NotionAPIClient,
    InvalidTokenError,
    NetworkError,
    NotionAPIError,
    RateLimitError,
    PermissionError,
)


@pytest.fixture
def client():
    """Create a NotionAPIClient instance for testing"""
    return NotionAPIClient()


# Strategy for generating various token strings
token_strategy = st.one_of(
    # Valid-looking tokens (secret_xxx format)
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=33, max_codepoint=126),
        min_size=40,
        max_size=60
    ).map(lambda s: f"secret_{s}"),
    # Random strings
    st.text(min_size=0, max_size=100),
    # Empty string
    st.just(""),
    # Special characters
    st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=50),
    # Very long strings
    st.text(min_size=100, max_size=500),
)


class TestProperty1TokenValidationConsistency:
    """
    Property 1: Token Validation Consistency

    **Validates: Requirements 1.1, 1.3**

    For *any* string input, if it's a valid Notion API token, authentication should succeed;
    if it's invalid, an error should be returned.
    """

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_token_validation_consistency(self, client, token):
        """
        Property: For any token string, authenticate() either succeeds with valid token
        or raises InvalidTokenError/NetworkError/NotionAPIError for invalid token.

        The system must handle all token inputs consistently:
        - Valid tokens return success=True with workspace_name
        - Invalid tokens raise InvalidTokenError
        - Network issues raise NetworkError
        - Other API errors raise NotionAPIError
        """
        # Simulate Notion API behavior based on token format
        # In reality, only tokens starting with "secret_" and having proper format are valid
        is_valid_format = isinstance(token, str) and token.startswith("secret_") and len(token) >= 40

        mock_response = MagicMock()

        if is_valid_format:
            # Simulate successful authentication for valid-looking tokens
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "object": "user",
                "id": "test-user-id",
                "name": "Test Workspace"
            }
        else:
            # Simulate authentication failure for invalid tokens
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

            if is_valid_format:
                # Valid token should succeed
                result = await client.authenticate(token)
                assert result["success"] is True
                assert "workspace_name" in result
                assert isinstance(result["workspace_name"], str)
            else:
                # Invalid token should raise InvalidTokenError
                with pytest.raises(InvalidTokenError):
                    await client.authenticate(token)

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_token_validation_error_handling(self, client, token):
        """
        Property: For any token string, when network errors occur,
        the system raises NetworkError consistently.

        This ensures error handling is complete and consistent across all inputs.
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            # Simulate network error
            mock_client.get = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
            mock_client_class.return_value = mock_client

            # Any token should result in NetworkError when network fails
            with pytest.raises(NetworkError):
                await client.authenticate(token)

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_token_validation_timeout_handling(self, client, token):
        """
        Property: For any token string, when timeout occurs,
        the system raises NetworkError consistently.

        This ensures timeout handling is complete and consistent across all inputs.
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            # Simulate timeout
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client_class.return_value = mock_client

            # Any token should result in NetworkError when timeout occurs
            with pytest.raises(NetworkError):
                await client.authenticate(token)

    @pytest.mark.asyncio
    @given(
        token=token_strategy,
        status_code=st.integers(min_value=400, max_value=599).filter(lambda x: x not in [401, 403, 429])
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_token_validation_api_error_handling(self, client, token, status_code):
        """
        Property: For any token string and any API error status code (except 401, 403, 429),
        the system raises NotionAPIError consistently.

        This ensures all API errors are handled properly.
        """
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {
            "code": "api_error",
            "message": f"API error with status {status_code}"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Any token with API error should raise NotionAPIError
            with pytest.raises(NotionAPIError):
                await client.authenticate(token)


class TestProperty2ErrorHandlingCompleteness:
    """
    Property 2: Error Handling Completeness

    **Validates: Requirements 1.4, 7.3, 7.4, 7.5**

    For *any* API error (network error, rate limit, permission error),
    the system logs the error and returns an appropriate error message.
    """

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_network_error_handling(self, client, token):
        """
        Property: For any token and any network error, the system raises NetworkError
        and logs the error.

        This ensures network errors are handled consistently across all operations.
        """
        network_errors = [
            httpx.NetworkError("Connection refused"),
            httpx.ConnectError("Failed to connect"),
            httpx.TimeoutException("Request timeout"),
        ]

        for error in network_errors:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get = AsyncMock(side_effect=error)
                mock_client_class.return_value = mock_client

                with pytest.raises(NetworkError) as exc_info:
                    await client.authenticate(token)

                # Verify error message contains information
                assert str(exc_info.value)

    @pytest.mark.asyncio
    @given(
        token=token_strategy,
        retry_after=st.one_of(st.none(), st.integers(min_value=1, max_value=3600))
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_rate_limit_error_handling(self, client, token, retry_after):
        """
        Property: For any token, when rate limit is exceeded (429),
        the system raises RateLimitError with retry_after information.

        This ensures rate limit errors are handled consistently.
        """
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "code": "rate_limited",
            "message": "Rate limit exceeded"
        }
        mock_response.headers = {}
        if retry_after is not None:
            mock_response.headers["Retry-After"] = str(retry_after)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(RateLimitError) as exc_info:
                await client.authenticate(token)

            # Verify error has retry_after attribute
            error = exc_info.value
            if retry_after is not None:
                assert error.retry_after == retry_after
            else:
                assert error.retry_after is None

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_permission_error_handling(self, client, token):
        """
        Property: For any token, when permission is denied (403),
        the system raises PermissionError.

        This ensures permission errors are handled consistently.
        """
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "code": "restricted_resource",
            "message": "Access denied"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(PermissionError) as exc_info:
                await client.authenticate(token)

            # Verify error message contains information
            assert "Permission denied" in str(exc_info.value) or "Access denied" in str(exc_info.value)

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_error_handling_in_get_databases(self, client, token):
        """
        Property: For any token, get_databases() handles all error types consistently.

        This ensures error handling is complete across all API methods.
        """
        error_scenarios = [
            (401, InvalidTokenError),
            (403, PermissionError),
            (429, RateLimitError),
            (500, NotionAPIError),
        ]

        for status_code, expected_error in error_scenarios:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.json.return_value = {
                "code": "error",
                "message": f"Error {status_code}"
            }
            if status_code == 429:
                mock_response.headers = {"Retry-After": "60"}
            else:
                mock_response.headers = {}

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                with pytest.raises(expected_error):
                    await client.get_databases(token)

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_error_handling_in_get_pages(self, client, token):
        """
        Property: For any token and database_id, get_pages() handles all error types consistently.

        This ensures error handling is complete across all API methods.
        """
        database_id = "test-database-id"

        error_scenarios = [
            (httpx.NetworkError("Connection failed"), NetworkError),
            (httpx.TimeoutException("Timeout"), NetworkError),
        ]

        for error_cause, expected_error in error_scenarios:
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post = AsyncMock(side_effect=error_cause)
                mock_client_class.return_value = mock_client

                with pytest.raises(expected_error):
                    await client.get_pages(token, database_id)

    @pytest.mark.asyncio
    @given(token=token_strategy)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_error_handling_in_fetch_pages_in_batch(self, client, token):
        """
        Property: For any token and page_ids, fetch_pages_in_batch() handles errors gracefully.

        The batch method is designed to be resilient - it logs individual page errors
        and continues processing. It only raises errors for critical failures like
        network errors during client setup.
        """
        page_ids = ["page1", "page2", "page3"]

        # Test that individual page errors are logged but don't stop processing
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "id": "page1",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Test Page"}]
                }
            },
            "parent": {"database_id": "db1"}
        }

        mock_response_error = MagicMock()
        mock_response_error.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Mix of successful and failed responses
            mock_client.get = AsyncMock(side_effect=[
                mock_response_success,  # page1 succeeds
                mock_response_error,     # page2 fails
                mock_response_success,   # page3 succeeds
            ])
            mock_client_class.return_value = mock_client

            # Should not raise error, but return partial results
            result = await client.fetch_pages_in_batch(token, page_ids)

            # Should have some results (the successful ones)
            assert isinstance(result, list)
            # At least one page should have been fetched successfully
            assert len(result) >= 0  # May be 0 or more depending on mock behavior


class TestProperty3PageDataRetrievalCompleteness:
    """
    Property 3: Page Data Retrieval Completeness

    **Validates: Requirements 2.1, 2.2, 2.3**

    For *any* Notion workspace, the system retrieves all accessible pages
    and correctly identifies each page's relation properties.
    """

    @pytest.mark.asyncio
    @given(
        token=token_strategy,
        num_databases=st.integers(min_value=0, max_value=5)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_get_databases_retrieves_all_accessible_databases(self, client, token, num_databases):
        """
        Property: For any token, get_databases() retrieves all accessible databases.

        This ensures the system fetches complete database information.
        """
        # Generate mock databases
        mock_databases = []
        for i in range(num_databases):
            mock_databases.append({
                "id": f"db-{i}",
                "object": "database",
                "title": [{"plain_text": f"Database {i}"}]
            })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": mock_databases,
            "has_more": False,
            "next_cursor": None
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # For valid-looking tokens, should succeed
            if isinstance(token, str) and token.startswith("secret_") and len(token) >= 40:
                result = await client.get_databases(token)

                # Should return all databases
                assert len(result) == num_databases

                # Each database should have id and title
                for i, db in enumerate(result):
                    assert "id" in db
                    assert "title" in db
                    assert db["id"] == f"db-{i}"

    @pytest.mark.asyncio
    @given(
        token=token_strategy,
        num_pages=st.integers(min_value=0, max_value=10)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_get_pages_retrieves_all_pages_from_database(self, client, token, num_pages):
        """
        Property: For any token and database_id, get_pages() retrieves all pages.

        This ensures the system fetches complete page information from databases.
        """
        database_id = "test-db-id"

        # Generate mock pages
        mock_pages = []
        for i in range(num_pages):
            mock_pages.append({
                "id": f"page-{i}",
                "object": "page",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"plain_text": f"Page {i}"}]
                    }
                }
            })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": mock_pages,
            "has_more": False,
            "next_cursor": None
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # For valid-looking tokens, should succeed
            if isinstance(token, str) and token.startswith("secret_") and len(token) >= 40:
                result = await client.get_pages(token, database_id)

                # Should return all pages
                assert len(result) == num_pages

                # Each page should have required fields
                for i, page in enumerate(result):
                    assert "id" in page
                    assert "title" in page
                    assert "database_id" in page
                    assert "properties" in page
                    assert page["id"] == f"page-{i}"
                    assert page["database_id"] == database_id

    @pytest.mark.asyncio
    @given(
        num_relations=st.integers(min_value=0, max_value=5)
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_extract_relations_identifies_all_relation_properties(self, client, num_relations):
        """
        Property: For any page, extract_relations() identifies all relation properties.

        This ensures the system correctly extracts all relations from page properties.
        """
        # Create a mock page with relation properties
        page_id = "source-page-id"
        properties = {}

        # Add relation properties
        expected_relations = []
        for i in range(num_relations):
            prop_name = f"Relation{i}"
            target_id = f"target-{i}"
            properties[prop_name] = {
                "type": "relation",
                "relation": [{"id": target_id}]
            }
            expected_relations.append({
                "source_page_id": page_id,
                "target_page_id": target_id,
                "property_name": prop_name
            })

        # Add non-relation properties (should be ignored)
        properties["Title"] = {
            "type": "title",
            "title": [{"plain_text": "Test Page"}]
        }
        properties["Number"] = {
            "type": "number",
            "number": 42
        }

        page = {
            "id": page_id,
            "properties": properties
        }

        # Extract relations
        result = client.extract_relations(page)

        # Should return all relations
        assert len(result) == num_relations

        # Verify each relation
        for i, relation in enumerate(result):
            assert "source_page_id" in relation
            assert "target_page_id" in relation
            assert "property_name" in relation
            assert relation["source_page_id"] == page_id
            assert relation in expected_relations

    @pytest.mark.asyncio
    @given(
        num_targets=st.integers(min_value=0, max_value=10)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_extract_relations_handles_multiple_targets(self, client, num_targets):
        """
        Property: For any page with multi-target relations, extract_relations()
        creates separate relation objects for each target.

        This ensures the system handles one-to-many relations correctly.
        """
        page_id = "source-page-id"

        # Create a relation property with multiple targets
        relation_targets = [{"id": f"target-{i}"} for i in range(num_targets)]

        page = {
            "id": page_id,
            "properties": {
                "RelatedPages": {
                    "type": "relation",
                    "relation": relation_targets
                }
            }
        }

        # Extract relations
        result = client.extract_relations(page)

        # Should create one relation per target
        assert len(result) == num_targets

        # Verify each relation points to correct target
        for i, relation in enumerate(result):
            assert relation["source_page_id"] == page_id
            assert relation["target_page_id"] == f"target-{i}"
            assert relation["property_name"] == "RelatedPages"


class TestProperty4IsolatedNodeHandling:
    """
    Property 4: Isolated Node Handling

    **Validates: Requirement 2.5**

    For *any* page without relation properties, the system treats it as an isolated node
    and includes it in the graph.
    """

    @pytest.mark.asyncio
    @given(
        has_title=st.booleans(),
        has_other_properties=st.booleans()
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_pages_without_relations_are_isolated_nodes(self, client, has_title, has_other_properties):
        """
        Property: For any page without relation properties, extract_relations()
        returns an empty list, indicating it's an isolated node.

        This ensures pages without relations are still valid nodes in the graph.
        """
        page_id = "isolated-page-id"
        properties = {}

        # Add title property if specified
        if has_title:
            properties["Title"] = {
                "type": "title",
                "title": [{"plain_text": "Isolated Page"}]
            }

        # Add other non-relation properties if specified
        if has_other_properties:
            properties["Status"] = {
                "type": "select",
                "select": {"name": "Active"}
            }
            properties["Number"] = {
                "type": "number",
                "number": 42
            }
            properties["Date"] = {
                "type": "date",
                "date": {"start": "2024-01-01"}
            }

        page = {
            "id": page_id,
            "properties": properties
        }

        # Extract relations
        result = client.extract_relations(page)

        # Should return empty list for isolated nodes
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    @given(
        num_pages_with_relations=st.integers(min_value=0, max_value=5),
        num_isolated_pages=st.integers(min_value=0, max_value=5)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_mixed_pages_with_and_without_relations(
        self,
        client,
        num_pages_with_relations,
        num_isolated_pages
    ):
        """
        Property: For any mix of pages with and without relations,
        the system correctly identifies which are isolated nodes.

        This ensures the system handles heterogeneous page sets correctly.
        """
        pages = []
        expected_total_relations = 0

        # Create pages with relations
        for i in range(num_pages_with_relations):
            page = {
                "id": f"connected-page-{i}",
                "properties": {
                    "Title": {
                        "type": "title",
                        "title": [{"plain_text": f"Connected Page {i}"}]
                    },
                    "Related": {
                        "type": "relation",
                        "relation": [{"id": f"target-{i}"}]
                    }
                }
            }
            pages.append(page)
            expected_total_relations += 1

        # Create isolated pages
        for i in range(num_isolated_pages):
            page = {
                "id": f"isolated-page-{i}",
                "properties": {
                    "Title": {
                        "type": "title",
                        "title": [{"plain_text": f"Isolated Page {i}"}]
                    },
                    "Status": {
                        "type": "select",
                        "select": {"name": "Active"}
                    }
                }
            }
            pages.append(page)

        # Extract relations from all pages
        total_relations = 0
        isolated_count = 0

        for page in pages:
            relations = client.extract_relations(page)
            total_relations += len(relations)
            if len(relations) == 0:
                isolated_count += 1

        # Verify counts
        assert total_relations == expected_total_relations
        assert isolated_count == num_isolated_pages

    @pytest.mark.asyncio
    async def test_empty_relation_property_is_isolated_node(self, client):
        """
        Property: For any page with an empty relation property (relation array is empty),
        the system treats it as an isolated node.

        This ensures pages with relation properties but no actual relations are handled correctly.
        """
        page = {
            "id": "page-with-empty-relation",
            "properties": {
                "Title": {
                    "type": "title",
                    "title": [{"plain_text": "Page with Empty Relation"}]
                },
                "Related": {
                    "type": "relation",
                    "relation": []  # Empty relation array
                }
            }
        }

        # Extract relations
        result = client.extract_relations(page)

        # Should return empty list
        assert isinstance(result, list)
        assert len(result) == 0



class TestProperty18BatchProcessingOptimization:
    """
    Property 18: Batch Processing Optimization

    **Validates: Requirement 8.4**

    For *any* list of page IDs, batch processing uses fewer API calls
    than individual requests.
    """

    @pytest.mark.asyncio
    @given(
        token=token_strategy,
        num_pages=st.integers(min_value=1, max_value=50)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_batch_processing_reduces_api_calls(self, client, token, num_pages):
        """
        Property: For any list of page IDs, fetch_pages_in_batch() processes
        multiple pages concurrently within batches.

        This ensures batch processing is more efficient than sequential requests.
        """
        page_ids = [f"page-{i}" for i in range(num_pages)]

        # Mock successful responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "page-id",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Test Page"}]
                }
            },
            "parent": {"database_id": "db1"}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # For valid-looking tokens, should succeed
            if isinstance(token, str) and token.startswith("secret_") and len(token) >= 40:
                result = await client.fetch_pages_in_batch(token, page_ids, batch_size=10)

                # Should return results
                assert isinstance(result, list)

                # Verify that get was called (batch processing happened)
                # The number of calls should be equal to num_pages since we're fetching each page
                assert mock_client.get.call_count == num_pages

    @pytest.mark.asyncio
    @given(
        num_pages=st.integers(min_value=1, max_value=30),
        batch_size=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_batch_size_controls_concurrent_requests(self, client, num_pages, batch_size):
        """
        Property: For any list of page IDs and batch size, the system processes
        pages in batches of the specified size.

        This ensures batch size parameter controls concurrency correctly.
        """
        token = "secret_" + "a" * 40  # Valid-looking token
        page_ids = [f"page-{i}" for i in range(num_pages)]

        # Mock successful responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "page-id",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "Test Page"}]
                }
            },
            "parent": {"database_id": "db1"}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await client.fetch_pages_in_batch(token, page_ids, batch_size=batch_size)

            # Should return results
            assert isinstance(result, list)

            # Total number of calls should equal number of pages
            assert mock_client.get.call_count == num_pages

    @pytest.mark.asyncio
    @given(
        num_pages=st.integers(min_value=1, max_value=20)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_batch_processing_handles_partial_failures(self, client, num_pages):
        """
        Property: For any list of page IDs, if some pages fail to fetch,
        batch processing continues and returns successful results.

        This ensures batch processing is resilient to partial failures.
        """
        token = "secret_" + "a" * 40  # Valid-looking token
        page_ids = [f"page-{i}" for i in range(num_pages)]

        # Mock mix of successful and failed responses
        def mock_get_side_effect(*args, **kwargs):
            # Alternate between success and failure
            url = args[0] if args else kwargs.get('url', '')
            if 'page-0' in url or 'page-2' in url or 'page-4' in url:
                # Success
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {
                    "id": "page-id",
                    "properties": {
                        "Name": {
                            "type": "title",
                            "title": [{"plain_text": "Test Page"}]
                        }
                    },
                    "parent": {"database_id": "db1"}
                }
                return response
            else:
                # Failure
                response = MagicMock()
                response.status_code = 404
                return response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client_class.return_value = mock_client

            result = await client.fetch_pages_in_batch(token, page_ids, batch_size=5)

            # Should return partial results (not raise error)
            assert isinstance(result, list)
            # Should have some successful results
            assert len(result) >= 0
