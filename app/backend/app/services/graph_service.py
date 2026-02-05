"""
Graph Service for transforming Notion data into graph format.
"""
import logging
from typing import List, Dict, Any, Set, Union, Callable
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.services.notion_client import notion_client, NotionAPIError
from app.services.cache_manager import cache_manager
from app.models.notion_token import NotionToken
from app.services.auth_service import auth_service


# Configure logging
logger = logging.getLogger(__name__)


class GraphService:
    """Service for transforming Notion data into graph format."""

    async def get_graph_data(
        self,
        db: Session,
        user_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Get graph data for a user, using cache if available.

        Args:
            db: Database session
            user_id: User ID (string or UUID)

        Returns:
            Graph data with nodes, edges, and databases

        Raises:
            Exception: If data fetching fails
        """
        # Check cache first
        cached_data = await cache_manager.get_graph_data(db, user_id)
        if cached_data:
            logger.info(f"Returning cached graph data for user {user_id}")
            return cached_data

        # Fetch fresh data
        logger.info(f"Fetching fresh graph data for user {user_id}")
        graph_data = await self._fetch_and_transform_data(db, user_id)

        # Cache the data
        await cache_manager.cache_graph_data(db, user_id, graph_data)

        return graph_data

    async def get_graph_data_progressive(
        self,
        db: Session,
        user_id: Union[str, UUID],
        yield_progress: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Get graph data with progressive loading and progress callbacks.

        This method implements progressive data loading by:
        1. Returning cached data immediately if available
        2. Fetching fresh data from Notion API
        3. Yielding progress updates as each database completes

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            yield_progress: Callback function to report progress updates.
                           Called with dict containing progress information.

        Returns:
            Complete graph data with metadata about failures:
            {
                "nodes": [...],
                "edges": [...],
                "databases": [...],
                "metadata": {
                    "total_databases": int,
                    "successful_databases": int,
                    "failed_databases": [{"id": str, "title": str, "error": str}, ...],
                    "fetched_at": str (ISO format)
                }
            }

        Raises:
            Exception: If token not found or critical errors occur
        """
        # Get all cached database data first
        cached_databases = await cache_manager.get_all_cached_databases(db, user_id)

        if cached_databases:
            # Merge cached data and yield immediately
            cached_graph = self._merge_database_data(cached_databases)

            # Find the most recent cache timestamp
            cached_at = None
            for db_data in cached_databases.values():
                # The data structure includes pages and database info
                # We need to check if there's a cached_at timestamp
                if isinstance(db_data, dict):
                    # For now, use current time as we don't store cached_at in the data itself
                    # The CachedDatabaseData model has cached_at but it's not in the returned data
                    pass

            yield_progress({
                "type": "cached_data",
                "data": cached_graph,
                "message": "Showing cached data while fetching updates"
            })
            logger.info(f"Yielded cached data for user {user_id} with {len(cached_databases)} databases")

        # Fetch fresh data with progress updates
        logger.info(f"Fetching fresh graph data progressively for user {user_id}")
        result = await self._fetch_and_transform_data_progressive(
            db, user_id, yield_progress
        )

        return result

    def _merge_database_data(
        self,
        cached_databases: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge per-database cached data into complete graph structure.

        Args:
            cached_databases: Dictionary mapping database_id to cached data
                             Each entry should have 'pages' and 'database' keys

        Returns:
            Complete graph data with nodes, edges, and databases
        """
        # Collect all pages and databases from cached data
        all_pages = []
        all_databases = []

        for database_id, db_data in cached_databases.items():
            if isinstance(db_data, dict):
                # Extract pages
                pages = db_data.get('pages', [])
                all_pages.extend(pages)

                # Extract database info
                database = db_data.get('database')
                if database:
                    all_databases.append(database)

        # Transform data into graph format
        nodes = self._transform_pages_to_nodes(all_pages)
        edges = self._transform_relations_to_edges(all_pages)
        database_list = self._transform_databases(all_databases)

        logger.info(
            f"Merged cached data: {len(all_pages)} pages, "
            f"{len(nodes)} nodes, {len(edges)} edges, "
            f"{len(database_list)} databases"
        )

        return {
            "nodes": nodes,
            "edges": edges,
            "databases": database_list
        }

    async def _fetch_and_transform_data(
        self,
        db: Session,
        user_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """
        Fetch data from Notion API and transform it into graph format.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Graph data with nodes, edges, and databases

        Raises:
            Exception: If token not found or API call fails
        """
        # Get user's Notion token
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if not stored_token:
            raise Exception("No Notion token found for user")

        # Decrypt token
        token = auth_service.decrypt_notion_token(stored_token.encrypted_token)

        # Fetch databases
        databases = await notion_client.get_databases(token)
        logger.info(f"Fetched {len(databases)} databases")

        # Fetch pages from all databases
        all_pages = []
        for database in databases:
            try:
                pages = await notion_client.get_pages(token, database["id"])
                all_pages.extend(pages)
                logger.info(f"Fetched {len(pages)} pages from database {database['id']}")
            except NotionAPIError as e:
                logger.warning(f"Failed to fetch pages from database {database['id']}: {str(e)}")
                continue

        # Transform data
        nodes = self._transform_pages_to_nodes(all_pages)
        edges = self._transform_relations_to_edges(all_pages)
        database_list = self._transform_databases(databases)

        return {
            "nodes": nodes,
            "edges": edges,
            "databases": database_list
        }

    async def _fetch_and_transform_data_progressive(
        self,
        db: Session,
        user_id: Union[str, UUID],
        yield_progress: Callable[[Dict[str, Any]], None]
    ) -> Dict[str, Any]:
        """
        Fetch data progressively, yielding results as databases complete.

        This method fetches data from multiple databases and yields progress
        updates after each database completes. It handles failures gracefully
        by continuing with remaining databases and using cached data as fallback.

        Args:
            db: Database session
            user_id: User ID
            yield_progress: Callback function to report progress

        Returns:
            Complete graph data with metadata:
            {
                "nodes": [...],
                "edges": [...],
                "databases": [...],
                "metadata": {
                    "total_databases": int,
                    "successful_databases": int,
                    "failed_databases": [{"id": str, "title": str, "error": str}, ...],
                    "fetched_at": str (ISO format)
                }
            }

        Raises:
            Exception: If token not found
        """
        # Get user's Notion token
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if not stored_token:
            raise Exception("No Notion token found for user")

        # Decrypt token
        token = auth_service.decrypt_notion_token(stored_token.encrypted_token)

        # Fetch databases
        databases = await notion_client.get_databases(token)
        total_databases = len(databases)
        logger.info(f"Fetched {total_databases} databases for progressive loading")

        # Yield progress: databases fetched
        yield_progress({
            "type": "databases_fetched",
            "total": total_databases
        })

        # Fetch pages from each database with progress tracking
        all_pages = []
        successful_databases = []
        failed_databases = []

        for idx, database in enumerate(databases):
            database_id = database["id"]
            database_title = database.get("title", "Untitled")

            try:
                # Fetch pages for this database
                pages = await notion_client.get_pages(token, database_id)
                all_pages.extend(pages)
                successful_databases.append(database)

                # Cache this database's data
                await cache_manager.cache_database_data(
                    db, user_id, database_id,
                    {"pages": pages, "database": database}
                )

                # Yield progress: database completed
                yield_progress({
                    "type": "database_completed",
                    "database_id": database_id,
                    "database_name": database_title,
                    "page_count": len(pages),
                    "progress": (idx + 1) / total_databases
                })

                logger.info(
                    f"Successfully fetched {len(pages)} pages from database "
                    f"{database_id} ({idx + 1}/{total_databases})"
                )

            except NotionAPIError as e:
                error_msg = str(e)
                logger.warning(
                    f"Failed to fetch pages from database {database_id} "
                    f"({database_title}): {error_msg}",
                    extra={
                        "database_id": database_id,
                        "database_title": database_title,
                        "error": error_msg,
                        "attempt": idx + 1,
                        "total": total_databases
                    }
                )

                # Try to use cached data for this database
                cached_db_data = await cache_manager.get_database_data(
                    db, user_id, database_id
                )

                if cached_db_data:
                    # Use cached data as fallback
                    cached_pages = cached_db_data.get("pages", [])
                    all_pages.extend(cached_pages)
                    successful_databases.append(database)

                    # Yield progress: using cached data
                    yield_progress({
                        "type": "database_from_cache",
                        "database_id": database_id,
                        "database_name": database_title,
                        "page_count": len(cached_pages),
                        "progress": (idx + 1) / total_databases
                    })

                    logger.info(
                        f"Using cached data for database {database_id} "
                        f"({len(cached_pages)} pages)",
                        extra={
                            "database_id": database_id,
                            "database_title": database_title,
                            "cached_page_count": len(cached_pages),
                            "fallback": True
                        }
                    )
                else:
                    # No cached data available, record as failed
                    failed_databases.append({
                        "id": database_id,
                        "title": database_title,
                        "error": error_msg
                    })

                    logger.warning(
                        f"No cached data available for failed database {database_id}",
                        extra={
                            "database_id": database_id,
                            "database_title": database_title,
                            "has_cache": False
                        }
                    )

        # Transform all collected data
        nodes = self._transform_pages_to_nodes(all_pages)
        edges = self._transform_relations_to_edges(all_pages)
        database_list = self._transform_databases(successful_databases)

        # Build result with metadata
        result = {
            "nodes": nodes,
            "edges": edges,
            "databases": database_list,
            "metadata": {
                "total_databases": total_databases,
                "successful_databases": len(successful_databases),
                "failed_databases": failed_databases,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        }

        logger.info(
            f"Progressive fetch complete: {len(successful_databases)}/{total_databases} "
            f"databases successful, {len(failed_databases)} failed, "
            f"{len(nodes)} nodes, {len(edges)} edges",
            extra={
                "total_databases": total_databases,
                "successful_databases": len(successful_databases),
                "failed_databases_count": len(failed_databases),
                "failed_database_ids": [db["id"] for db in failed_databases],
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        )
            f"databases successful, {len(failed_databases)} failed, "
            f"{len(nodes)} nodes, {len(edges)} edges"
        )

        return result

    def _transform_pages_to_nodes(
        self,
        pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform Notion pages into node format.

        Args:
            pages: List of Notion page objects

        Returns:
            List of node objects
        """
        nodes = []
        for page in pages:
            node = {
                "id": page["id"],
                "title": page["title"],
                "databaseId": page["database_id"],
                "x": 0.0,  # Will be set by layout algorithm on frontend
                "y": 0.0,  # Will be set by layout algorithm on frontend
                "visible": True
            }
            nodes.append(node)

        logger.info(f"Transformed {len(nodes)} pages to nodes")
        return nodes

    def _transform_relations_to_edges(
        self,
        pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform Notion relations into edge format.

        Args:
            pages: List of Notion page objects

        Returns:
            List of edge objects
        """
        edges = []
        edge_id_counter = 0

        # Create a set of valid page IDs for validation
        valid_page_ids = {page["id"] for page in pages}

        for page in pages:
            relations = notion_client.extract_relations(page)

            for relation in relations:
                source_id = relation["source_page_id"]
                target_id = relation["target_page_id"]

                # Only create edge if both nodes exist in our graph
                if source_id in valid_page_ids and target_id in valid_page_ids:
                    edge = {
                        "id": f"edge_{edge_id_counter}",
                        "sourceId": source_id,
                        "targetId": target_id,
                        "relationProperty": relation["property_name"],
                        "visible": True
                    }
                    edges.append(edge)
                    edge_id_counter += 1

        logger.info(f"Transformed {len(edges)} relations to edges")
        return edges

    def _transform_databases(
        self,
        databases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform Notion databases into database format.

        Args:
            databases: List of Notion database objects

        Returns:
            List of database objects
        """
        database_list = []
        for db in databases:
            database = {
                "id": db["id"],
                "title": db["title"],
                "hidden": False
            }
            database_list.append(database)

        logger.info(f"Transformed {len(database_list)} databases")
        return database_list

    async def get_databases(
        self,
        db: Session,
        user_id: Union[str, UUID]
    ) -> List[Dict[str, Any]]:
        """
        Get list of databases for a user.

        Args:
            db: Database session
            user_id: User ID (string or UUID)

        Returns:
            List of database objects

        Raises:
            Exception: If token not found or API call fails
        """
        # Get user's Notion token
        stored_token = db.query(NotionToken).filter(
            NotionToken.user_id == user_id
        ).first()

        if not stored_token:
            raise Exception("No Notion token found for user")

        # Decrypt token
        token = auth_service.decrypt_notion_token(stored_token.encrypted_token)

        # Fetch databases
        databases = await notion_client.get_databases(token)

        # Transform to expected format
        return self._transform_databases(databases)


# Create a singleton instance
graph_service = GraphService()
