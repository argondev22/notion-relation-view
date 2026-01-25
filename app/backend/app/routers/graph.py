"""
Graph API router for fetching graph data and databases.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.graph_service import graph_service
from app.services.notion_client import InvalidTokenError, NetworkError, NotionAPIError
from app.models.user import User


router = APIRouter(prefix="/api/graph", tags=["graph"])


class NodeResponse(BaseModel):
    """Response model for a graph node"""
    id: str
    title: str
    databaseId: str
    x: float
    y: float
    visible: bool


class EdgeResponse(BaseModel):
    """Response model for a graph edge"""
    id: str
    sourceId: str
    targetId: str
    relationProperty: str
    visible: bool


class DatabaseResponse(BaseModel):
    """Response model for a database"""
    id: str
    title: str
    hidden: bool


class GraphDataResponse(BaseModel):
    """Response model for complete graph data"""
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    databases: List[DatabaseResponse]


@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete graph data for the current user.

    Fetches all accessible pages and relations from the user's Notion workspace
    and transforms them into graph format (nodes, edges, databases).

    Uses caching to minimize API calls (TTL: 15 minutes).

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Complete graph data with nodes, edges, and databases

    Raises:
        HTTPException: If no token is stored or data fetching fails
    """
    try:
        # Get graph data (uses cache if available)
        graph_data = await graph_service.get_graph_data(db, current_user.id)

        return GraphDataResponse(
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
            databases=graph_data["databases"]
        )

    except Exception as e:
        error_message = str(e)

        if "No Notion token" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Notion token found. Please save your Notion API token first."
            )
        elif isinstance(e, InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Notion API token. Please update your token."
            )
        elif isinstance(e, NetworkError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network error while fetching data: {error_message}"
            )
        elif isinstance(e, NotionAPIError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Notion API error: {error_message}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch graph data: {error_message}"
            )


@router.get("/databases", response_model=List[DatabaseResponse])
async def get_databases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of databases for the current user.

    Fetches all accessible databases from the user's Notion workspace.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of databases

    Raises:
        HTTPException: If no token is stored or data fetching fails
    """
    try:
        # Get databases
        databases = await graph_service.get_databases(db, current_user.id)

        return [DatabaseResponse(**db) for db in databases]

    except Exception as e:
        error_message = str(e)

        if "No Notion token" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Notion token found. Please save your Notion API token first."
            )
        elif isinstance(e, InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Notion API token. Please update your token."
            )
        elif isinstance(e, NetworkError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network error while fetching databases: {error_message}"
            )
        elif isinstance(e, NotionAPIError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Notion API error: {error_message}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch databases: {error_message}"
            )
