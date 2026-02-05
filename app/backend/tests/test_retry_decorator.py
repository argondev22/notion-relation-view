"""
Tests for retry decorator with exponential backoff
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from datetime import datetime

from app.services.notion_client import (
    with_retry,
    InvalidTokenError,
    NetworkError,
    RateLimitError,
    PermissionError,
    NotionAPIError
)


class TestRetryDecorator:
    """Tests for with_retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test that function succeeds on first attempt without retry"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_timeout_with_exponential_backoff(self):
        """Test retry with timeout error and exponential backoff"""
        call_count = 0
        call_times = []

        @with_retry(max_retries=3, base_delay=0.01, exponential_base=2.0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            call_times.append(datetime.now())
            if call_count < 3:
                raise httpx.TimeoutException("Request timeout")
            return "success"

        result = await failing_function()
        assert result == "success"
        assert call_count == 3

        # Verify exponential backoff timing (approximately)
        # Attempt 1: immediate
        # Attempt 2: after ~0.01s (base_delay * 2^0)
        # Attempt 3: after ~0.02s (base_delay * 2^1)
        if len(call_times) >= 3:
            delay1 = (call_times[1] - call_times[0]).total_seconds()
            delay2 = (call_times[2] - call_times[1]).total_seconds()
            # Allow some tolerance for timing
            assert delay1 >= 0.008  # ~0.01s
            assert delay2 >= 0.016  # ~0.02s

    @pytest.mark.asyncio
    async def test_retry_network_error_exhausts_retries(self):
        """Test that network errors exhaust retries and raise"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise httpx.NetworkError("Connection failed")

        with pytest.raises(httpx.NetworkError, match="Connection failed"):
            await always_failing_function()

        # Should be called 4 times: initial + 3 retries
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_retry_rate_limit_with_retry_after(self):
        """Test rate limit error respects Retry-After header"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited", retry_after=0.02)
            return "success"

        start_time = datetime.now()
        result = await rate_limited_function()
        elapsed = (datetime.now() - start_time).total_seconds()

        assert result == "success"
        assert call_count == 2
        # Should wait at least the retry_after duration
        assert elapsed >= 0.018  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_retry_rate_limit_without_retry_after(self):
        """Test rate limit error uses exponential backoff when no Retry-After"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited", retry_after=None)
            return "success"

        result = await rate_limited_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_permanent_error_no_retry(self):
        """Test that permanent errors (InvalidToken, Permission) are not retried"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def invalid_token_function():
            nonlocal call_count
            call_count += 1
            raise InvalidTokenError("Invalid token")

        with pytest.raises(InvalidTokenError, match="Invalid token"):
            await invalid_token_function()

        # Should only be called once (no retries for permanent errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_permission_error_no_retry(self):
        """Test that permission errors are not retried"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def permission_error_function():
            nonlocal call_count
            call_count += 1
            raise PermissionError("Permission denied")

        with pytest.raises(PermissionError, match="Permission denied"):
            await permission_error_function()

        # Should only be called once (no retries for permanent errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_unexpected_error_no_retry(self):
        """Test that unexpected errors are not retried"""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        async def unexpected_error_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Unexpected error")

        with pytest.raises(ValueError, match="Unexpected error"):
            await unexpected_error_function()

        # Should only be called once (no retries for unexpected errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        call_count = 0
        call_times = []

        @with_retry(max_retries=5, base_delay=1.0, max_delay=0.05, exponential_base=2.0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            call_times.append(datetime.now())
            if call_count < 4:
                raise httpx.TimeoutException("Timeout")
            return "success"

        result = await failing_function()
        assert result == "success"
        assert call_count == 4

        # Verify that delays are capped at max_delay
        # Without cap: 1.0, 2.0, 4.0 seconds
        # With cap of 0.05: 0.05, 0.05, 0.05 seconds
        if len(call_times) >= 3:
            delay1 = (call_times[1] - call_times[0]).total_seconds()
            delay2 = (call_times[2] - call_times[1]).total_seconds()
            # All delays should be close to max_delay (0.05s)
            assert delay1 <= 0.08  # Should be capped
            assert delay2 <= 0.08  # Should be capped

    @pytest.mark.asyncio
    async def test_retry_configurable_parameters(self):
        """Test that retry parameters are configurable"""
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01, exponential_base=3.0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"

        result = await failing_function()
        assert result == "success"
        # Should be called 3 times: initial + 2 retries
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_logging(self, caplog):
        """Test that retry attempts are logged"""
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Timeout")
            return "success"

        with caplog.at_level("WARNING"):
            result = await failing_function()

        assert result == "success"
        # Check that warning was logged for retry
        assert any("Retrying in" in record.message for record in caplog.records)
        assert any("TimeoutException" in record.message for record in caplog.records)
