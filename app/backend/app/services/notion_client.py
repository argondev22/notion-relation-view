"""
Notion API Client for fetching databases, pages, and relations.
"""
import logging
from typing import List, Dict, Any, Optional, TypeVar, Callable
from datetime import datetime
from functools import wraps
import asyncio
import httpx
from app.config import settings


# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar('T')


class NotionAPIError(Exception):
    """Base exception for Notion API errors."""
    pass


class InvalidTokenError(NotionAPIError):
    """Raised when the Notion API token is invalid."""
    pass


class NetworkError(NotionAPIError):
    """Raised when a network error occurs."""
    pass


class RateLimitError(NotionAPIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermissionError(NotionAPIError):
    """Raised when permission is denied for a resource."""
    pass


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for retrying async functions with exponential backoff.

    This decorator handles transient errors (timeouts, network errors) by retrying
    the decorated function with exponentially increasing delays between attempts.
    Rate limit errors are handled specially by respecting the Retry-After header.
    Permanent errors (invalid token, permission denied) are not retried.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2.0)

    Returns:
        Decorated async function with retry logic

    Example:
        @with_retry(max_retries=3, base_delay=1.0)
        async def fetch_data():
            # Function that may fail transiently
            pass

    Retry behavior:
        - Attempt 0: No delay (initial attempt)
        - Attempt 1: base_delay * (exponential_base ^ 0) = 1.0s
        - Attempt 2: base_delay * (exponential_base ^ 1) = 2.0s
        - Attempt 3: base_delay * (exponential_base ^ 2) = 4.0s

    Error handling:
        - httpx.TimeoutException: Retried with exponential backoff
        - httpx.NetworkError: Retried with exponential backoff
        - RateLimitError: Retried after waiting for retry_after duration
        - InvalidTokenError: Not retried (permanent error)
        - PermissionError: Not retried (permanent error)
        - Other exceptions: Not retried
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            correlation_id = id(wrapper)  # Simple correlation ID for log tracing

            for attempt in range(max_retries + 1):
                try:
                    # Log attempt if it's a retry
                    if attempt > 0:
                        logger.info(
                            f"[{correlation_id}] Retry attempt {attempt}/{max_retries} "
                            f"for {func.__name__}"
                        )

                    # Execute the function
                    return await func(*args, **kwargs)

                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exception = e
                    error_type = type(e).__name__

                    # Log timeout with detailed context
                    if isinstance(e, httpx.TimeoutException):
                        logger.error(
                            f"[{correlation_id}] Timeout in {func.__name__}: "
                            f"Operation timed out after attempt {attempt + 1}/{max_retries + 1}. "
                            f"Error: {error_type}: {str(e)}",
                            extra={
                                "correlation_id": correlation_id,
                                "operation": func.__name__,
                                "error_type": error_type,
                                "attempt": attempt + 1,
                                "max_retries": max_retries + 1
                            }
                        )

                    # Don't retry if we've exhausted all attempts
                    if attempt == max_retries:
                        logger.error(
                            f"[{correlation_id}] All retry attempts exhausted for {func.__name__}. "
                            f"Final error: {error_type}: {str(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )

                    logger.warning(
                        f"[{correlation_id}] Attempt {attempt + 1}/{max_retries + 1} failed "
                        f"for {func.__name__}: {error_type}: {str(e)}. "
                        f"Retrying in {delay:.2f}s...",
                        extra={
                            "correlation_id": correlation_id,
                            "operation": func.__name__,
                            "attempt": attempt + 1,
                            "backoff_delay": delay
                        }
                    )

                    await asyncio.sleep(delay)

                except RateLimitError as e:
                    last_exception = e

                    # Don't retry if we've exhausted all attempts
                    if attempt == max_retries:
                        logger.error(
                            f"[{correlation_id}] All retry attempts exhausted for {func.__name__}. "
                            f"Rate limit error: {str(e)}"
                        )
                        raise

                    # Use retry_after from the error if available, otherwise use exponential backoff
                    if e.retry_after:
                        delay = float(e.retry_after)
                        logger.warning(
                            f"[{correlation_id}] Rate limited on attempt {attempt + 1}/{max_retries + 1} "
                            f"for {func.__name__}. Waiting {delay}s as specified by Retry-After header..."
                        )
                    else:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        logger.warning(
                            f"[{correlation_id}] Rate limited on attempt {attempt + 1}/{max_retries + 1} "
                            f"for {func.__name__}. No Retry-After header, using exponential backoff: {delay:.2f}s..."
                        )

                    await asyncio.sleep(delay)

                except (InvalidTokenError, PermissionError) as e:
                    # These are permanent errors - don't retry
                    logger.error(
                        f"[{correlation_id}] Permanent error in {func.__name__}: "
                        f"{type(e).__name__}: {str(e)}. Not retrying."
                    )
                    raise

                except Exception as e:
                    # Unexpected errors - don't retry
                    logger.error(
                        f"[{correlation_id}] Unexpected error in {func.__name__}: "
                        f"{type(e).__name__}: {str(e)}. Not retrying."
                    )
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Retry logic failed unexpectedly for {func.__name__}")

        return wrapper
    return decorator


class NotionAPIClient:
    """Client for interacting with the Notion API."""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self):
        """
        Initialize the Notion API client with configurable timeouts.

        Timeouts can be configured via environment variables:
        - NOTION_TIMEOUT_DATABASE_LIST: Timeout for listing databases (default: 60s)
        - NOTION_TIMEOUT_DATABASE_QUERY: Timeout for querying database pages (default: 90s)
        - NOTION_TIMEOUT_PAGE_FETCH: Timeout for fetching individual pages (default: 30s)
        """
        # Load timeout configuration from settings
        self.timeout_database_list = settings.NOTION_TIMEOUT_DATABASE_LIST
        self.timeout_database_query = settings.NOTION_TIMEOUT_DATABASE_QUERY
        self.timeout_page_fetch = settings.NOTION_TIMEOUT_PAGE_FETCH

        logger.info(
            f"NotionAPIClient initialized with timeouts: "
            f"database_list={self.timeout_database_list}s, "
            f"database_query={self.timeout_database_query}s, "
            f"page_fetch={self.timeout_page_fetch}s"
        )

    def _get_headers(self, token: str) -> Dict[str, str]:
        """
        Get headers for Notion API requests.

        Args:
            token: Notion API token

        Returns:
            Dictionary of headers
        """
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def _handle_error_response(self, response: httpx.Response, operation: str = "unknown", database_id: str = None) -> None:
        """
        Handle error responses from Notion API with comprehensive logging.

        Args:
            response: HTTP response object
            operation: Type of operation being performed (e.g., "get_databases", "get_pages")
            database_id: Database ID if applicable

        Raises:
            InvalidTokenError: If token is invalid (401)
            PermissionError: If permission is denied (403)
            RateLimitError: If rate limit is exceeded (429)
            NotionAPIError: For other API errors
        """
        status_code = response.status_code
        request_url = str(response.request.url)
        request_method = response.request.method

        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = error_data.get("code", "unknown")
        except Exception:
            error_message = response.text or "Unknown error"
            error_code = "unknown"

        # Comprehensive error logging with all required fields
        log_context = {
            "operation": operation,
            "request_url": request_url,
            "request_method": request_method,
            "status_code": status_code,
            "error_code": error_code,
            "error_message": error_message,
        }

        if database_id:
            log_context["database_id"] = database_id

        logger.error(
            f"Notion API error - Operation: {operation}, "
            f"URL: {request_url}, Method: {request_method}, "
            f"Status: {status_code}, Code: {error_code}, "
            f"Message: {error_message}" +
            (f", Database: {database_id}" if database_id else ""),
            extra=log_context
        )

        if status_code == 401:
            raise InvalidTokenError(f"Invalid Notion API token: {error_message}")
        elif status_code == 403:
            raise PermissionError(f"Permission denied: {error_message}")
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_seconds = int(retry_after) if retry_after else None
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                retry_after=retry_after_seconds
            )
        else:
            raise NotionAPIError(f"Notion API error ({status_code}): {error_message}")

    async def authenticate(self, token: str) -> Dict[str, Any]:
        """
        Verify the Notion API token by fetching user information.

        Args:
            token: Notion API token

        Returns:
            Dictionary with authentication result:
            {
                "success": bool,
                "workspace_name": str (optional),
                "error": str (optional)
            }

        Raises:
            InvalidTokenError: If token is invalid
            NetworkError: If network error occurs
            NotionAPIError: For other API errors
        """
        try:
            # Use database list timeout for authentication
            timeout = httpx.Timeout(self.timeout_database_list, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try to fetch the bot user to verify the token
                response = await client.get(
                    f"{self.BASE_URL}/users/me",
                    headers=self._get_headers(token)
                )

                if response.status_code == 200:
                    user_data = response.json()
                    workspace_name = user_data.get("name", "Unknown Workspace")
                    logger.info(f"Successfully authenticated with Notion API")
                    return {
                        "success": True,
                        "workspace_name": workspace_name
                    }
                else:
                    self._handle_error_response(response)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout while authenticating: {str(e)}")
            raise NetworkError(f"Request timeout: {str(e)}")
        except httpx.NetworkError as e:
            logger.error(f"Network error while authenticating: {str(e)}")
            raise NetworkError(f"Network error: {str(e)}")
        except (InvalidTokenError, PermissionError, RateLimitError, NotionAPIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error while authenticating: {str(e)}")
            raise NotionAPIError(f"Unexpected error: {str(e)}")

    @with_retry(max_retries=3, base_delay=1.0)
    async def get_databases(self, token: str) -> List[Dict[str, Any]]:
        """
        Fetch all accessible databases from Notion.

        Args:
            token: Notion API token

        Returns:
            List of database objects with id and title

        Raises:
            InvalidTokenError: If token is invalid
            NetworkError: If network error occurs
            NotionAPIError: For other API errors
        """
        databases = []

        try:
            # Use database list timeout for fetching databases
            timeout = httpx.Timeout(self.timeout_database_list, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                has_more = True
                start_cursor = None

                while has_more:
                    # Search for databases
                    payload = {
                        "filter": {
                            "value": "database",
                            "property": "object"
                        },
                        "page_size": 100
                    }

                    if start_cursor:
                        payload["start_cursor"] = start_cursor

                    response = await client.post(
                        f"{self.BASE_URL}/search",
                        headers=self._get_headers(token),
                        json=payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])

                        for db in results:
                            database_id = db.get("id")
                            title_property = db.get("title", [])
                            title = ""
                            if title_property:
                                title = "".join([t.get("plain_text", "") for t in title_property])

                            databases.append({
                                "id": database_id,
                                "title": title or "Untitled Database"
                            })

                        has_more = data.get("has_more", False)
                        start_cursor = data.get("next_cursor")
                    else:
                        self._handle_error_response(response)

                logger.info(f"Fetched {len(databases)} databases")
                return databases

        except httpx.TimeoutException as e:
            logger.error(f"Timeout while fetching databases: {str(e)}")
            raise NetworkError(f"Request timeout: {str(e)}")
        except httpx.NetworkError as e:
            logger.error(f"Network error while fetching databases: {str(e)}")
            raise NetworkError(f"Network error: {str(e)}")
        except (InvalidTokenError, PermissionError, RateLimitError, NotionAPIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching databases: {str(e)}")
            raise NotionAPIError(f"Unexpected error: {str(e)}")

    @with_retry(max_retries=3, base_delay=2.0)
    async def get_pages(self, token: str, database_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all pages from a specific database.

        Args:
            token: Notion API token
            database_id: Database ID to fetch pages from

        Returns:
            List of page objects with id, title, database_id, and properties

        Raises:
            InvalidTokenError: If token is invalid
            NetworkError: If network error occurs
            NotionAPIError: For other API errors
        """
        pages = []

        try:
            # Use database query timeout for fetching pages from a database
            timeout = httpx.Timeout(self.timeout_database_query, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                has_more = True
                start_cursor = None

                while has_more:
                    payload = {
                        "page_size": 100
                    }

                    if start_cursor:
                        payload["start_cursor"] = start_cursor

                    response = await client.post(
                        f"{self.BASE_URL}/databases/{database_id}/query",
                        headers=self._get_headers(token),
                        json=payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])

                        for page in results:
                            page_id = page.get("id")
                            properties = page.get("properties", {})

                            # Extract title from properties
                            title = self._extract_title_from_properties(properties)

                            pages.append({
                                "id": page_id,
                                "title": title,
                                "database_id": database_id,
                                "properties": properties
                            })

                        has_more = data.get("has_more", False)
                        start_cursor = data.get("next_cursor")
                    else:
                        self._handle_error_response(response)

                logger.info(f"Fetched {len(pages)} pages from database {database_id}")
                return pages

        except httpx.TimeoutException as e:
            logger.error(f"Timeout while fetching pages: {str(e)}")
            raise NetworkError(f"Request timeout: {str(e)}")
        except httpx.NetworkError as e:
            logger.error(f"Network error while fetching pages: {str(e)}")
            raise NetworkError(f"Network error: {str(e)}")
        except (InvalidTokenError, PermissionError, RateLimitError, NotionAPIError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching pages: {str(e)}")
            raise NotionAPIError(f"Unexpected error: {str(e)}")

    def _extract_title_from_properties(self, properties: Dict[str, Any]) -> str:
        """
        Extract the title from page properties.

        Args:
            properties: Page properties dictionary

        Returns:
            Page title string
        """
        # Look for title property
        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type")
            if prop_type == "title":
                title_content = prop_value.get("title", [])
                if title_content:
                    return "".join([t.get("plain_text", "") for t in title_content])

        return "Untitled"

    def extract_relations(self, page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract relation properties from a page.

        Args:
            page: Page object with properties

        Returns:
            List of relation objects:
            [
                {
                    "source_page_id": str,
                    "target_page_id": str,
                    "property_name": str
                }
            ]
        """
        relations = []
        source_page_id = page.get("id")
        properties = page.get("properties", {})

        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type")

            if prop_type == "relation":
                relation_data = prop_value.get("relation", [])
                for relation in relation_data:
                    target_page_id = relation.get("id")
                    if target_page_id:
                        relations.append({
                            "source_page_id": source_page_id,
                            "target_page_id": target_page_id,
                            "property_name": prop_name
                        })

        return relations

    async def fetch_pages_in_batch(
        self,
        token: str,
        page_ids: List[str],
        batch_size: int = 10,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple pages by their IDs in optimized batches with concurrency control.

        Args:
            token: Notion API token
            page_ids: List of page IDs to fetch
            batch_size: Number of pages to fetch concurrently (default: 10)
            max_concurrent: Maximum concurrent requests (default: 5)

        Returns:
            List of page objects

        Raises:
            InvalidTokenError: If token is invalid
            NetworkError: If network error occurs
            NotionAPIError: For other API errors
        """
        import asyncio

        pages = []
        total_requests = 0

        try:
            # Use page fetch timeout for individual page requests
            timeout = httpx.Timeout(self.timeout_page_fetch, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Create semaphore to limit concurrent requests
                semaphore = asyncio.Semaphore(max_concurrent)

                async def fetch_page(page_id: str) -> Optional[Dict[str, Any]]:
                    """Fetch a single page with semaphore control."""
                    nonlocal total_requests

                    async with semaphore:
                        try:
                            total_requests += 1
                            response = await client.get(
                                f"{self.BASE_URL}/pages/{page_id}",
                                headers=self._get_headers(token)
                            )

                            if response.status_code == 200:
                                page_data = response.json()
                                properties = page_data.get("properties", {})
                                title = self._extract_title_from_properties(properties)

                                return {
                                    "id": page_data.get("id"),
                                    "title": title,
                                    "database_id": page_data.get("parent", {}).get("database_id"),
                                    "properties": properties
                                }
                            else:
                                # Log error but continue with other pages
                                logger.warning(
                                    f"Failed to fetch page {page_id}: {response.status_code}"
                                )
                                return None
                        except Exception as e:
                            logger.warning(f"Error fetching page {page_id}: {str(e)}")
                            return None

                # Process pages in batches
                for i in range(0, len(page_ids), batch_size):
                    batch = page_ids[i:i + batch_size]

                    # Fetch batch concurrently
                    tasks = [fetch_page(page_id) for page_id in batch]
                    batch_results = await asyncio.gather(*tasks)

                    # Filter out None results
                    pages.extend([page for page in batch_results if page is not None])

                logger.info(
                    f"Fetched {len(pages)}/{len(page_ids)} pages in batch mode "
                    f"with {total_requests} API requests (optimization: "
                    f"{len(page_ids) - total_requests} requests saved)"
                )
                return pages

        except httpx.TimeoutException as e:
            logger.error(f"Timeout while fetching pages in batch: {str(e)}")
            raise NetworkError(f"Request timeout: {str(e)}")
        except httpx.NetworkError as e:
            logger.error(f"Network error while fetching pages in batch: {str(e)}")
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching pages in batch: {str(e)}")
            raise NotionAPIError(f"Unexpected error: {str(e)}")


# Create a singleton instance
notion_client = NotionAPIClient()
