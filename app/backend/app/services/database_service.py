"""
Database Service for managing database operations.

This service provides methods for managing views and other database entities
with optimized query performance.
"""
from typing import List, Optional
from uuid import UUID
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.view import View
from app.models.user import User


class DatabaseService:
    """Service for handling database operations with performance optimizations."""

    def create_view(
        self,
        db: Session,
        user_id: str,
        name: str,
        database_ids: List[str],
        zoom_level: float = 1.0,
        pan_x: float = 0.0,
        pan_y: float = 0.0
    ) -> View:
        """
        Create a new view with a unique ID.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            name: View name
            database_ids: List of database IDs to display
            zoom_level: Zoom level (default: 1.0)
            pan_x: Pan position X (default: 0.0)
            pan_y: Pan position Y (default: 0.0)

        Returns:
            Created View object

        Raises:
            ValueError: If user does not exist
        """
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id_uuid = UUID(user_id)
        else:
            user_id_uuid = user_id

        # Verify user exists (optimized query - only check existence)
        user_exists = db.query(User.id).filter(User.id == user_id_uuid).first()
        if not user_exists:
            raise ValueError(f"User with id {user_id} does not exist")

        # Create new view with auto-generated UUID
        view = View(
            user_id=user_id_uuid,
            name=name,
            database_ids=database_ids,
            zoom_level=zoom_level,
            pan_x=pan_x,
            pan_y=pan_y
        )

        db.add(view)
        db.commit()
        db.refresh(view)

        return view

    def get_views(self, db: Session, user_id: str, limit: Optional[int] = None) -> List[View]:
        """
        Get all views for a user with optional limit.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            limit: Maximum number of views to return (optional)

        Returns:
            List of View objects
        """
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id_uuid = UUID(user_id)
        else:
            user_id_uuid = user_id

        query = db.query(View).filter(View.user_id == user_id_uuid).order_by(View.created_at.desc())

        if limit:
            query = query.limit(limit)

        views = query.all()
        return views

    def get_view(self, db: Session, view_id: str) -> Optional[View]:
        """
        Get a specific view by ID with optimized query.

        Args:
            db: Database session
            view_id: View ID (string or UUID)

        Returns:
            View object if found, None otherwise
        """
        # Convert view_id to UUID if it's a string
        if isinstance(view_id, str):
            view_id_uuid = UUID(view_id)
        else:
            view_id_uuid = view_id

        # Optimized query - only fetch what we need
        view = db.query(View).filter(View.id == view_id_uuid).first()
        return view

    def get_views_by_ids(self, db: Session, view_ids: List[str]) -> List[View]:
        """
        Get multiple views by their IDs in a single query.

        Args:
            db: Database session
            view_ids: List of view IDs (strings or UUIDs)

        Returns:
            List of View objects
        """
        # Convert all IDs to UUIDs
        view_id_uuids = [UUID(vid) if isinstance(vid, str) else vid for vid in view_ids]

        # Fetch all views in a single query
        views = db.query(View).filter(View.id.in_(view_id_uuids)).all()
        return views

    def update_view(
        self,
        db: Session,
        view_id: str,
        name: Optional[str] = None,
        database_ids: Optional[List[str]] = None,
        zoom_level: Optional[float] = None,
        pan_x: Optional[float] = None,
        pan_y: Optional[float] = None
    ) -> View:
        """
        Update a view.

        Args:
            db: Database session
            view_id: View ID (string or UUID)
            name: New view name (optional)
            database_ids: New list of database IDs (optional)
            zoom_level: New zoom level (optional)
            pan_x: New pan position X (optional)
            pan_y: New pan position Y (optional)

        Returns:
            Updated View object

        Raises:
            ValueError: If view does not exist
        """
        # Convert view_id to UUID if it's a string
        if isinstance(view_id, str):
            view_id_uuid = UUID(view_id)
        else:
            view_id_uuid = view_id

        # Get existing view
        view = db.query(View).filter(View.id == view_id_uuid).first()
        if not view:
            raise ValueError(f"View with id {view_id} does not exist")

        # Update fields if provided
        if name is not None:
            view.name = name
        if database_ids is not None:
            view.database_ids = database_ids
        if zoom_level is not None:
            view.zoom_level = zoom_level
        if pan_x is not None:
            view.pan_x = pan_x
        if pan_y is not None:
            view.pan_y = pan_y

        db.commit()
        db.refresh(view)

        return view

    def delete_view(self, db: Session, view_id: str) -> None:
        """
        Delete a view.

        Args:
            db: Database session
            view_id: View ID (string or UUID)

        Raises:
            ValueError: If view does not exist
        """
        # Convert view_id to UUID if it's a string
        if isinstance(view_id, str):
            view_id_uuid = UUID(view_id)
        else:
            view_id_uuid = view_id

        # Get existing view
        view = db.query(View).filter(View.id == view_id_uuid).first()
        if not view:
            raise ValueError(f"View with id {view_id} does not exist")

        db.delete(view)
        db.commit()


# Create a singleton instance
database_service = DatabaseService()
