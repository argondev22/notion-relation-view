"""
Cache Manager for storing and retrieving graph data.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# Configure logging
logger = logging.getLogger(__name__)


class CachedGraphData(Base):
    """Model for cached graph data."""
    __tablename__ = "cached_graph_data"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    data = Column(JSON, nullable=False)
    cached_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class CacheManager:
    """Manager for caching graph data."""

    DEFAULT_TTL_MINUTES = 15

    def __init__(self, ttl_minutes: int = DEFAULT_TTL_MINUTES):
        """
        Initialize the cache manager.

        Args:
            ttl_minutes: Time-to-live for cached data in minutes (default: 15)
        """
        self.ttl_minutes = ttl_minutes

    async def cache_graph_data(
        self,
        db: Session,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Cache graph data for a user.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            data: Graph data to cache

        Raises:
            Exception: If caching fails
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=self.ttl_minutes)

            # Check if cache entry exists
            cached_entry = db.query(CachedGraphData).filter(
                CachedGraphData.user_id == user_id
            ).first()

            if cached_entry:
                # Update existing cache
                cached_entry.data = data
                cached_entry.cached_at = now
                cached_entry.expires_at = expires_at
            else:
                # Create new cache entry
                new_cache = CachedGraphData(
                    user_id=user_id,
                    data=data,
                    cached_at=now,
                    expires_at=expires_at
                )
                db.add(new_cache)

            db.commit()
            logger.info(f"Cached graph data for user {user_id}, expires at {expires_at}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cache graph data for user {user_id}: {str(e)}")
            raise

    async def get_graph_data(
        self,
        db: Session,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached graph data for a user.

        Args:
            db: Database session
            user_id: User ID (string or UUID)

        Returns:
            Cached graph data if valid, None otherwise
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            cached_entry = db.query(CachedGraphData).filter(
                CachedGraphData.user_id == user_id
            ).first()

            if not cached_entry:
                logger.info(f"No cached data found for user {user_id}")
                return None

            # Check if cache is still valid
            now = datetime.utcnow()
            if now > cached_entry.expires_at:
                logger.info(f"Cache expired for user {user_id}")
                # Delete expired cache
                db.delete(cached_entry)
                db.commit()
                return None

            logger.info(f"Retrieved cached graph data for user {user_id}")
            return cached_entry.data

        except Exception as e:
            logger.error(f"Failed to retrieve cached data for user {user_id}: {str(e)}")
            return None

    async def invalidate_cache(
        self,
        db: Session,
        user_id: str
    ) -> None:
        """
        Invalidate (delete) cached graph data for a user.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            cached_entry = db.query(CachedGraphData).filter(
                CachedGraphData.user_id == user_id
            ).first()

            if cached_entry:
                db.delete(cached_entry)
                db.commit()
                logger.info(f"Invalidated cache for user {user_id}")
            else:
                logger.info(f"No cache to invalidate for user {user_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to invalidate cache for user {user_id}: {str(e)}")
            raise

    async def is_cache_valid(
        self,
        db: Session,
        user_id: str
    ) -> bool:
        """
        Check if cached data exists and is still valid.

        Args:
            db: Database session
            user_id: User ID (string or UUID)

        Returns:
            True if cache is valid, False otherwise
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            cached_entry = db.query(CachedGraphData).filter(
                CachedGraphData.user_id == user_id
            ).first()

            if not cached_entry:
                return False

            now = datetime.utcnow()
            is_valid = now <= cached_entry.expires_at

            logger.info(f"Cache validity for user {user_id}: {is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Failed to check cache validity for user {user_id}: {str(e)}")
            return False


# Create a singleton instance
cache_manager = CacheManager()
