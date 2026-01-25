"""
Cache Manager for storing and retrieving graph data.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Index
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
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)


class CacheManager:
    """Manager for caching graph data with optimized performance."""

    DEFAULT_TTL_MINUTES = 15
    # Adaptive TTL based on data size
    SMALL_DATA_TTL_MINUTES = 30  # < 100 nodes
    MEDIUM_DATA_TTL_MINUTES = 20  # 100-500 nodes
    LARGE_DATA_TTL_MINUTES = 15  # > 500 nodes

    def __init__(self, ttl_minutes: int = DEFAULT_TTL_MINUTES):
        """
        Initialize the cache manager.

        Args:
            ttl_minutes: Time-to-live for cached data in minutes (default: 15)
        """
        self.ttl_minutes = ttl_minutes

    def _calculate_adaptive_ttl(self, data: Dict[str, Any]) -> int:
        """
        Calculate adaptive TTL based on data size.

        Args:
            data: Graph data

        Returns:
            TTL in minutes
        """
        node_count = len(data.get('nodes', []))

        if node_count < 100:
            return self.SMALL_DATA_TTL_MINUTES
        elif node_count < 500:
            return self.MEDIUM_DATA_TTL_MINUTES
        else:
            return self.LARGE_DATA_TTL_MINUTES

    async def cache_graph_data(
        self,
        db: Session,
        user_id: str,
        data: Dict[str, Any],
        use_adaptive_ttl: bool = True
    ) -> None:
        """
        Cache graph data for a user with optimized storage.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            data: Graph data to cache
            use_adaptive_ttl: Use adaptive TTL based on data size (default: True)

        Raises:
            Exception: If caching fails
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            now = datetime.utcnow()

            # Calculate TTL
            if use_adaptive_ttl:
                ttl_minutes = self._calculate_adaptive_ttl(data)
            else:
                ttl_minutes = self.ttl_minutes

            expires_at = now + timedelta(minutes=ttl_minutes)

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
            logger.info(
                f"Cached graph data for user {user_id}, "
                f"nodes={len(data.get('nodes', []))}, "
                f"ttl={ttl_minutes}min, expires at {expires_at}"
            )

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

    async def cleanup_expired_cache(self, db: Session) -> int:
        """
        Clean up all expired cache entries.

        Args:
            db: Database session

        Returns:
            Number of entries deleted
        """
        try:
            now = datetime.utcnow()

            # Delete all expired entries
            deleted_count = db.query(CachedGraphData).filter(
                CachedGraphData.expires_at < now
            ).delete()

            db.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")

            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup expired cache: {str(e)}")
            return 0


# Create a singleton instance
cache_manager = CacheManager()
