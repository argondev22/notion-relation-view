"""
Notion API Client for fetching databases, pages, and relations.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from app.config import settings


# Configure logging
logger = logging.getLogger(__name__)


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


class NotionAPIClient:
    """Client for interacting with the Notion API."""

    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self):
        """Initialize the Notion API client."""
        self.timeout = httpx.Timeout(30.0, connect=10.0)

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

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle error responses from Notion API.

        Args:
            response: HTTP response object

        Raises:
            InvalidTokenError: If token is invalid (401)
            PermissionError: If permission is denied (403)
            RateLimitError: If rate limit is exceeded (429)
            NotionAPIError: For other API errors
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = error_data.get("code", "unknown")
        except Exception:
            error_message = response.text or "Unknown error"
            error_code = "unknown"

        logger.error(
            f"Notion API error: status={status_code}, code={error_code}, message={error_message}"
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
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
