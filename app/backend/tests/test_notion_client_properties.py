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
