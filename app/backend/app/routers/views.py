"""
Views API router for managing view configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import logging

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.database_service import database_service
from app.services.graph_service import graph_service
from app.models.user import User

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/views", tags=["views"])


class CreateViewRequest(BaseModel):
    """Request model for creating a view"""
    name: str
    database_ids: List[str]
    zoom_level: Optional[float] = 1.0
    pan_x: Optional[float] = 0.0
    pan_y: Optional[float] = 0.0


class UpdateViewRequest(BaseModel):
    """Request model for updating a view"""
    name: Optional[str] = None
    database_ids: Optional[List[str]] = None
    zoom_level: Optional[float] = None
    pan_x: Optional[float] = None
    pan_y: Optional[float] = None


class ViewResponse(BaseModel):
    """Response model for a view"""
    id: str
    user_id: str
    name: str
    database_ids: List[str]
    zoom_level: float
    pan_x: float
    pan_y: float
    url: str

    class Config:
        from_attributes = True


class FailedDatabase(BaseModel):
    """Model for a database that failed to load"""
    id: str
    title: str
    error: str


class GraphMetadata(BaseModel):
    """Metadata about graph data fetch operation"""
    total_databases: int
    successful_databases: int
    failed_databases: List[FailedDatabase]
    fetched_at: str
    from_cache: bool = False


class GraphDataResponse(BaseModel):
    """Response model for graph data with metadata"""
    nodes: List[dict]
    edges: List[dict]
    databases: List[dict]
    metadata: Optional[GraphMetadata] = None


@router.post("", response_model=ViewResponse, status_code=status.HTTP_201_CREATED)
async def create_view(
    request: CreateViewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new view configuration.

    Args:
        request: View creation request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created view with unique ID and URL

    Raises:
        HTTPException: If view creation fails
    """
    try:
        # Create view
        view = database_service.create_view(
            db=db,
            user_id=str(current_user.id),
            name=request.name,
            database_ids=request.database_ids,
            zoom_level=request.zoom_level,
            pan_x=request.pan_x,
            pan_y=request.pan_y
        )

        # Generate view URL
        view_url = f"/view/{view.id}"

        return ViewResponse(
            id=str(view.id),
            user_id=str(view.user_id),
            name=view.name,
            database_ids=view.database_ids,
            zoom_level=view.zoom_level,
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            url=view_url
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create view: {str(e)}"
        )


@router.get("", response_model=List[ViewResponse])
async def get_views(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all views for the current user.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of views

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        views = database_service.get_views(db, str(current_user.id))

        return [
            ViewResponse(
                id=str(view.id),
                user_id=str(view.user_id),
                name=view.name,
                database_ids=view.database_ids,
                zoom_level=view.zoom_level,
                pan_x=view.pan_x,
                pan_y=view.pan_y,
                url=f"/view/{view.id}"
            )
            for view in views
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve views: {str(e)}"
        )


@router.get("/{view_id}", response_model=ViewResponse)
async def get_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific view by ID.

    Args:
        view_id: View ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        View details

    Raises:
        HTTPException: If view not found or access denied
    """
    try:
        view = database_service.get_view(db, view_id)

        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"View with id {view_id} not found"
            )

        # Verify user owns this view
        if str(view.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this view"
            )

        return ViewResponse(
            id=str(view.id),
            user_id=str(view.user_id),
            name=view.name,
            database_ids=view.database_ids,
            zoom_level=view.zoom_level,
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            url=f"/view/{view.id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve view: {str(e)}"
        )


@router.put("/{view_id}", response_model=ViewResponse)
async def update_view(
    view_id: str,
    request: UpdateViewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a view configuration.

    Args:
        view_id: View ID
        request: View update request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated view

    Raises:
        HTTPException: If view not found or access denied
    """
    try:
        # Check if view exists and user owns it
        existing_view = database_service.get_view(db, view_id)

        if not existing_view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"View with id {view_id} not found"
            )

        if str(existing_view.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this view"
            )

        # Update view
        view = database_service.update_view(
            db=db,
            view_id=view_id,
            name=request.name,
            database_ids=request.database_ids,
            zoom_level=request.zoom_level,
            pan_x=request.pan_x,
            pan_y=request.pan_y
        )

        return ViewResponse(
            id=str(view.id),
            user_id=str(view.user_id),
            name=view.name,
            database_ids=view.database_ids,
            zoom_level=view.zoom_level,
            pan_x=view.pan_x,
            pan_y=view.pan_y,
            url=f"/view/{view.id}"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update view: {str(e)}"
        )


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a view.

    Args:
        view_id: View ID
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: If view not found or access denied
    """
    try:
        # Check if view exists and user owns it
        existing_view = database_service.get_view(db, view_id)

        if not existing_view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"View with id {view_id} not found"
            )

        if str(existing_view.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this view"
            )

        # Delete view
        database_service.delete_view(db, view_id)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete view: {str(e)}"
        )


def _filter_graph_data(
    graph_data: dict,
    selected_db_ids: List[str]
) -> dict:
    """
    Filter graph data by selected database IDs.

    This helper method filters nodes, edges, and databases to only include
    data from the specified databases. Edges are filtered to only include
    connections between visible nodes.

    Args:
        graph_data: Complete graph data with nodes, edges, databases, and optional metadata
        selected_db_ids: List of database IDs to include in the filtered result

    Returns:
        Filtered graph data with same structure as input:
        {
            "nodes": [...],  # Only nodes from selected databases
            "edges": [...],  # Only edges between visible nodes
            "databases": [...],  # Only selected databases
            "metadata": {...}  # Preserved if present
        }
    """
    selected_db_ids_set = set(selected_db_ids)

    # Filter nodes by database ID
    filtered_nodes = [
        node for node in graph_data.get("nodes", [])
        if node.get("databaseId") in selected_db_ids_set
    ]

    # Get set of visible node IDs
    filtered_node_ids = {node["id"] for node in filtered_nodes}

    # Filter edges to only include connections between visible nodes
    filtered_edges = [
        edge for edge in graph_data.get("edges", [])
        if edge.get("sourceId") in filtered_node_ids
        and edge.get("targetId") in filtered_node_ids
    ]

    # Filter databases list
    filtered_databases = [
        db for db in graph_data.get("databases", [])
        if db.get("id") in selected_db_ids_set
    ]

    # Build result with filtered data
    result = {
        "nodes": filtered_nodes,
        "edges": filtered_edges,
        "databases": filtered_databases
    }

    # Preserve metadata if present
    if "metadata" in graph_data:
        result["metadata"] = graph_data["metadata"]

    return result


@router.get("/{view_id}/data")
async def get_view_graph_data(
    view_id: str,
    stream: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get graph data for a specific view (public access via view URL).

    This endpoint allows public access to view data via the view URL,
    without requiring authentication. Supports both regular and streaming modes.

    Args:
        view_id: View ID
        stream: If True, stream progress updates via Server-Sent Events (default: False)
        db: Database session

    Returns:
        - If stream=False: GraphDataResponse with complete data
        - If stream=True: StreamingResponse with Server-Sent Events

    Raises:
        HTTPException: If view not found or data retrieval fails
    """
    try:
        # Get view
        view = database_service.get_view(db, view_id)

        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"View with id {view_id} not found"
            )

        # Validate view configuration
        if not view.database_ids or len(view.database_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This view has no databases selected. Please edit the view and select at least one database to display."
            )

        # Filter out any invalid database IDs (non-existent databases)
        # This is a soft validation - we'll just log a warning
        if view.database_ids:
            logger.info(f"View {view_id} configured with {len(view.database_ids)} databases")

        # Validate zoom and pan values, use defaults if invalid
        zoom_level = view.zoom_level if view.zoom_level and view.zoom_level > 0 else 1.0
        pan_x = view.pan_x if view.pan_x is not None else 0.0
        pan_y = view.pan_y if view.pan_y is not None else 0.0

        if zoom_level != view.zoom_level or pan_x != view.pan_x or pan_y != view.pan_y:
            logger.warning(
                f"View {view_id} has invalid zoom/pan values. "
                f"Using defaults: zoom={zoom_level}, pan_x={pan_x}, pan_y={pan_y}"
            )

        if stream:
            # Return streaming response with Server-Sent Events
            async def generate():
                try:
                    progress_updates = []

                    def yield_progress(update: dict):
                        """Callback to capture and send progress updates"""
                        progress_updates.append(update)
                        # Send as Server-Sent Event
                        event_data = json.dumps(update)
                        return f"data: {event_data}\n\n"

                    # Get data with progress callbacks
                    graph_data = await graph_service.get_graph_data_progressive(
                        db, str(view.user_id), yield_progress
                    )

                    # Yield all progress updates
                    for update in progress_updates:
                        event_data = json.dumps(update)
                        yield f"data: {event_data}\n\n"

                    # Filter by view's selected databases
                    filtered_data = _filter_graph_data(graph_data, view.database_ids)

                    # Send final complete event
                    final_event = json.dumps({
                        "type": "complete",
                        "data": filtered_data
                    })
                    yield f"data: {final_event}\n\n"

                except Exception as e:
                    logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
                    error_event = json.dumps({
                        "type": "error",
                        "error": str(e)
                    })
                    yield f"data: {error_event}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Return complete data (existing behavior for backward compatibility)
            graph_data = await graph_service.get_graph_data(db, str(view.user_id))

            # Filter by view's selected databases
            filtered_data = _filter_graph_data(graph_data, view.database_ids)

            return GraphDataResponse(**filtered_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving view graph data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve view graph data: {str(e)}"
        )
