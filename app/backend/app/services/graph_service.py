"""
Graph Service for transforming Notion data into graph format.
"""
import logging
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session

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
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get graph data for a user, using cache if available.

        Args:
            db: Database session
            user_id: User ID

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

    async def _fetch_and_transform_data(
        self,
        db: Session,
        user_id: str
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
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of databases for a user.

        Args:
            db: Database session
            user_id: User ID

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
