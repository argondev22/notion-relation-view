"""
Cache Manager for storing and retrieving graph data.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
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


class CachedDatabaseData(Base):
    """Model for per-database cached data."""
    __tablename__ = "cached_database_data"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    database_id = Column(String(255), primary_key=True)
    data = Column(JSON, nullable=False)
    cached_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('ix_cached_db_user_db', 'user_id', 'database_id'),
        Index('ix_cached_db_expires', 'expires_at'),
    )


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

    def _validate_timezone_aware(self, dt: datetime, field_name: str) -> None:
        """
        Validate that a datetime object is timezone-aware.

        Args:
            dt: Datetime object to validate
            field_name: Name of the field for error messages

        Raises:
            ValueError: If datetime is timezone-naive
        """
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise ValueError(
                f"{field_name} must be timezone-aware with UTC timezone. "
                f"Use datetime.now(timezone.utc) instead of datetime.utcnow()"
            )

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

            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "cached_at")

            # Calculate TTL
            if use_adaptive_ttl:
                ttl_minutes = self._calculate_adaptive_ttl(data)
            else:
                ttl_minutes = self.ttl_minutes

            expires_at = now + timedelta(minutes=ttl_minutes)
            self._validate_timezone_aware(expires_at, "expires_at")

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
            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "current_time")

            # Handle backward compatibility: if cached_entry.expires_at is timezone-naive,
            # convert it to timezone-aware for comparison
            expires_at = cached_entry.expires_at
            if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
                # Assume naive datetime is UTC and make it timezone-aware
                expires_at = expires_at.replace(tzinfo=timezone.utc)
                logger.warning(
                    f"Found timezone-naive expires_at for user {user_id}, "
                    f"treating as UTC for backward compatibility"
                )

            if now > expires_at:
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

            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "current_time")

            # Handle backward compatibility: if cached_entry.expires_at is timezone-naive,
            # convert it to timezone-aware for comparison
            expires_at = cached_entry.expires_at
            if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
                # Assume naive datetime is UTC and make it timezone-aware
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            is_valid = now <= expires_at

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
            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "current_time")

            # Fetch all cache entries to handle timezone-naive entries
            all_entries = db.query(CachedGraphData).all()
            deleted_count = 0

            for entry in all_entries:
                expires_at = entry.expires_at
                # Handle backward compatibility: if expires_at is timezone-naive,
                # convert it to timezone-aware for comparison
                if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if now > expires_at:
                    db.delete(entry)
                    deleted_count += 1

            db.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")

            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup expired cache: {str(e)}")
            return 0

    async def cache_database_data(
        self,
        db: Session,
        user_id: str,
        database_id: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Cache data for a specific database with adaptive TTL.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            database_id: Database ID to cache data for
            data: Database data to cache (should include 'pages' and 'database' keys)

        Raises:
            Exception: If caching fails
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "cached_at")

            # Calculate adaptive TTL based on number of pages in this database
            page_count = len(data.get('pages', []))

            # Use similar logic to graph data but based on page count
            if page_count < 100:
                ttl_minutes = self.SMALL_DATA_TTL_MINUTES
            elif page_count < 500:
                ttl_minutes = self.MEDIUM_DATA_TTL_MINUTES
            else:
                ttl_minutes = self.LARGE_DATA_TTL_MINUTES

            expires_at = now + timedelta(minutes=ttl_minutes)
            self._validate_timezone_aware(expires_at, "expires_at")

            # Check if cache entry exists
            cached_entry = db.query(CachedDatabaseData).filter(
                CachedDatabaseData.user_id == user_id,
                CachedDatabaseData.database_id == database_id
            ).first()

            if cached_entry:
                # Update existing cache
                cached_entry.data = data
                cached_entry.cached_at = now
                cached_entry.expires_at = expires_at
            else:
                # Create new cache entry
                new_cache = CachedDatabaseData(
                    user_id=user_id,
                    database_id=database_id,
                    data=data,
                    cached_at=now,
                    expires_at=expires_at
                )
                db.add(new_cache)

            db.commit()
            logger.info(
                f"Cached database data for user {user_id}, "
                f"database_id={database_id}, "
                f"pages={page_count}, "
                f"ttl={ttl_minutes}min, expires at {expires_at}"
            )

        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to cache database data for user {user_id}, "
                f"database_id={database_id}: {str(e)}"
            )
            raise

    async def get_database_data(
        self,
        db: Session,
        user_id: str,
        database_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data for a specific database.

        Args:
            db: Database session
            user_id: User ID (string or UUID)
            database_id: Database ID to retrieve cached data for

        Returns:
            Cached database data if valid, None otherwise
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            cached_entry = db.query(CachedDatabaseData).filter(
                CachedDatabaseData.user_id == user_id,
                CachedDatabaseData.database_id == database_id
            ).first()

            if not cached_entry:
                logger.info(
                    f"No cached data found for user {user_id}, "
                    f"database_id={database_id}"
                )
                return None

            # Check if cache is still valid
            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "current_time")

            # Handle backward compatibility: if cached_entry.expires_at is timezone-naive,
            # convert it to timezone-aware for comparison
            expires_at = cached_entry.expires_at
            if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
                # Assume naive datetime is UTC and make it timezone-aware
                expires_at = expires_at.replace(tzinfo=timezone.utc)
                logger.warning(
                    f"Found timezone-naive expires_at for user {user_id}, "
                    f"database_id={database_id}, treating as UTC for backward compatibility"
                )

            if now > expires_at:
                logger.info(
                    f"Cache expired for user {user_id}, database_id={database_id}"
                )
                # Delete expired cache
                db.delete(cached_entry)
                db.commit()
                return None

            logger.info(
                f"Retrieved cached database data for user {user_id}, "
                f"database_id={database_id}"
            )
            return cached_entry.data

        except Exception as e:
            logger.error(
                f"Failed to retrieve cached database data for user {user_id}, "
                f"database_id={database_id}: {str(e)}"
            )
            return None

    async def get_all_cached_databases(
        self,
        db: Session,
        user_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all cached database data for a user, filtering out expired entries.

        Args:
            db: Database session
            user_id: User ID (string or UUID)

        Returns:
            Dictionary mapping database_id to cached data. Returns empty dict if no valid cache exists.
        """
        try:
            import uuid
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            # Fetch all cached database entries for this user
            cached_entries = db.query(CachedDatabaseData).filter(
                CachedDatabaseData.user_id == user_id
            ).all()

            if not cached_entries:
                logger.info(f"No cached database data found for user {user_id}")
                return {}

            # Check current time for expiration comparison
            now = datetime.now(timezone.utc)
            self._validate_timezone_aware(now, "current_time")

            # Filter out expired entries and build result dictionary
            result = {}
            expired_entries = []

            for entry in cached_entries:
                # Handle backward compatibility: if expires_at is timezone-naive,
                # convert it to timezone-aware for comparison
                expires_at = entry.expires_at
                if expires_at.tzinfo is None or expires_at.tzinfo.utcoffset(expires_at) is None:
                    # Assume naive datetime is UTC and make it timezone-aware
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                    logger.warning(
                        f"Found timezone-naive expires_at for user {user_id}, "
                        f"database_id={entry.database_id}, treating as UTC for backward compatibility"
                    )

                # Check if entry is still valid
                if now <= expires_at:
                    # Add valid entry to result
                    result[entry.database_id] = entry.data
                else:
                    # Mark expired entry for deletion
                    expired_entries.append(entry)
                    logger.info(
                        f"Cache expired for user {user_id}, database_id={entry.database_id}"
                    )

            # Delete expired entries
            if expired_entries:
                for entry in expired_entries:
                    db.delete(entry)
                db.commit()
                logger.info(
                    f"Deleted {len(expired_entries)} expired database cache entries for user {user_id}"
                )

            logger.info(
                f"Retrieved {len(result)} valid cached databases for user {user_id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to retrieve all cached databases for user {user_id}: {str(e)}"
            )
            return {}


# Create a singleton instance
cache_manager = CacheManager()
