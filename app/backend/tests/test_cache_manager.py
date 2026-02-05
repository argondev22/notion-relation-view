"""
Unit tests for cache_manager service.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.services.cache_manager import cache_manager, CachedDatabaseData
from app.models.user import User
from app.services.auth_service import auth_service


@pytest.fixture
def db():
    """Create a database session for testing."""
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = auth_service.register(db, "test@example.com", "password123")
    return user


@pytest.mark.asyncio
async def test_cache_database_data_creates_new_entry(db: Session, test_user: User):
    """Test that cache_database_data creates a new cache entry."""
    database_id = "test-db-123"
    data = {
        "pages": [
            {"id": "page-1", "title": "Page 1"},
            {"id": "page-2", "title": "Page 2"}
        ],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # Cache the data
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, data)

    # Verify cache entry was created
    cached_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == database_id
    ).first()

    assert cached_entry is not None
    assert cached_entry.data == data
    # Note: SQLite doesn't preserve timezone info, but PostgreSQL does
    # The important thing is that the datetime objects exist and are valid
    assert cached_entry.cached_at is not None
    assert cached_entry.expires_at is not None
    assert cached_entry.expires_at > cached_entry.cached_at


@pytest.mark.asyncio
async def test_cache_database_data_updates_existing_entry(db: Session, test_user: User):
    """Test that cache_database_data updates an existing cache entry."""
    database_id = "test-db-456"

    # Create initial cache entry
    initial_data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": database_id, "title": "Test Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, initial_data)

    # Get the initial cached_at time
    initial_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == database_id
    ).first()
    initial_cached_at = initial_entry.cached_at

    # Update with new data
    updated_data = {
        "pages": [
            {"id": "page-1", "title": "Page 1"},
            {"id": "page-2", "title": "Page 2"},
            {"id": "page-3", "title": "Page 3"}
        ],
        "database": {"id": database_id, "title": "Test Database Updated"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, updated_data)

    # Verify cache entry was updated (not duplicated)
    all_entries = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == database_id
    ).all()

    assert len(all_entries) == 1
    assert all_entries[0].data == updated_data
    assert all_entries[0].cached_at >= initial_cached_at


@pytest.mark.asyncio
async def test_cache_database_data_uses_adaptive_ttl(db: Session, test_user: User):
    """Test that cache_database_data calculates adaptive TTL based on page count."""

    # Test small data (< 100 pages) - should get 30 min TTL
    small_data = {
        "pages": [{"id": f"page-{i}", "title": f"Page {i}"} for i in range(50)],
        "database": {"id": "small-db", "title": "Small Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), "small-db", small_data)

    small_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == "small-db"
    ).first()

    small_ttl = (small_entry.expires_at - small_entry.cached_at).total_seconds() / 60
    assert 29 <= small_ttl <= 31  # Allow 1 minute tolerance

    # Test medium data (100-500 pages) - should get 20 min TTL
    medium_data = {
        "pages": [{"id": f"page-{i}", "title": f"Page {i}"} for i in range(200)],
        "database": {"id": "medium-db", "title": "Medium Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), "medium-db", medium_data)

    medium_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == "medium-db"
    ).first()

    medium_ttl = (medium_entry.expires_at - medium_entry.cached_at).total_seconds() / 60
    assert 19 <= medium_ttl <= 21  # Allow 1 minute tolerance

    # Test large data (> 500 pages) - should get 15 min TTL
    large_data = {
        "pages": [{"id": f"page-{i}", "title": f"Page {i}"} for i in range(600)],
        "database": {"id": "large-db", "title": "Large Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), "large-db", large_data)

    large_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == "large-db"
    ).first()

    large_ttl = (large_entry.expires_at - large_entry.cached_at).total_seconds() / 60
    assert 14 <= large_ttl <= 16  # Allow 1 minute tolerance


@pytest.mark.asyncio
async def test_cache_database_data_uses_timezone_aware_datetime(db: Session, test_user: User):
    """Test that cache_database_data uses timezone-aware datetime objects internally.

    Note: SQLite doesn't preserve timezone info when storing, but PostgreSQL does.
    This test verifies the method creates timezone-aware datetimes before storage.
    """
    database_id = "test-db-timezone"
    data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # The method should use timezone-aware datetime internally
    # We can't verify this directly with SQLite, but we can verify the method
    # doesn't raise a ValueError from _validate_timezone_aware
    try:
        await cache_manager.cache_database_data(db, str(test_user.id), database_id, data)
        # If we get here, the method successfully used timezone-aware datetimes
        success = True
    except ValueError as e:
        if "timezone-aware" in str(e):
            success = False
        else:
            raise

    assert success, "Method should use timezone-aware datetime objects"

    # Verify cache entry was created
    cached_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == database_id
    ).first()

    assert cached_entry is not None
    assert cached_entry.data == data


@pytest.mark.asyncio
async def test_cache_database_data_handles_empty_pages(db: Session, test_user: User):
    """Test that cache_database_data handles databases with no pages."""
    database_id = "empty-db"
    data = {
        "pages": [],
        "database": {"id": database_id, "title": "Empty Database"}
    }

    await cache_manager.cache_database_data(db, str(test_user.id), database_id, data)

    cached_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == test_user.id,
        CachedDatabaseData.database_id == database_id
    ).first()

    assert cached_entry is not None
    assert cached_entry.data == data
    assert len(cached_entry.data["pages"]) == 0


@pytest.mark.asyncio
async def test_get_database_data_returns_valid_cache(db: Session, test_user: User):
    """Test that get_database_data returns cached data when valid."""
    database_id = "test-db-get-1"
    data = {
        "pages": [
            {"id": "page-1", "title": "Page 1"},
            {"id": "page-2", "title": "Page 2"}
        ],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # Cache the data
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, data)

    # Retrieve the cached data
    cached_data = await cache_manager.get_database_data(db, str(test_user.id), database_id)

    assert cached_data is not None
    assert cached_data == data
    assert len(cached_data["pages"]) == 2


@pytest.mark.asyncio
async def test_get_database_data_returns_none_when_not_found(db: Session, test_user: User):
    """Test that get_database_data returns None when no cache exists."""
    database_id = "non-existent-db"

    # Try to retrieve non-existent cache
    cached_data = await cache_manager.get_database_data(db, str(test_user.id), database_id)

    assert cached_data is None


@pytest.mark.asyncio
async def test_get_database_data_returns_none_when_expired(db: Session, test_user: User):
    """Test that get_database_data returns None and deletes expired cache."""
    database_id = "test-db-expired"
    data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # Create a cache entry that's already expired
    import uuid
    user_uuid = uuid.UUID(str(test_user.id))
    now = datetime.now(timezone.utc)
    expired_entry = CachedDatabaseData(
        user_id=user_uuid,
        database_id=database_id,
        data=data,
        cached_at=now - timedelta(hours=1),
        expires_at=now - timedelta(minutes=1)  # Expired 1 minute ago
    )
    db.add(expired_entry)
    db.commit()

    # Try to retrieve expired cache
    cached_data = await cache_manager.get_database_data(db, str(test_user.id), database_id)

    assert cached_data is None

    # Verify the expired entry was deleted
    remaining_entry = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == user_uuid,
        CachedDatabaseData.database_id == database_id
    ).first()

    assert remaining_entry is None


@pytest.mark.asyncio
async def test_get_database_data_uses_timezone_aware_comparison(db: Session, test_user: User):
    """Test that get_database_data uses timezone-aware datetime for expiration check."""
    database_id = "test-db-timezone-check"
    data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # Cache the data
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, data)

    # The method should use timezone-aware datetime for comparison
    # We can't verify this directly with SQLite, but we can verify the method
    # doesn't raise a TypeError about comparing naive and aware datetimes
    try:
        cached_data = await cache_manager.get_database_data(db, str(test_user.id), database_id)
        # If we get here, the method successfully used timezone-aware comparison
        success = True
    except TypeError as e:
        if "can't compare offset-naive and offset-aware datetimes" in str(e):
            success = False
        else:
            raise

    assert success, "Method should use timezone-aware datetime for comparison"
    assert cached_data is not None


@pytest.mark.asyncio
async def test_get_database_data_handles_backward_compatibility(db: Session, test_user: User):
    """Test that get_database_data handles timezone-naive expires_at for backward compatibility."""
    database_id = "test-db-backward-compat"
    data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": database_id, "title": "Test Database"}
    }

    # Create a cache entry with timezone-naive datetime (simulating old data)
    import uuid
    user_uuid = uuid.UUID(str(test_user.id))
    now_naive = datetime.utcnow()  # Timezone-naive
    expired_entry = CachedDatabaseData(
        user_id=user_uuid,
        database_id=database_id,
        data=data,
        cached_at=now_naive,
        expires_at=now_naive + timedelta(minutes=30)  # Still valid
    )
    db.add(expired_entry)
    db.commit()

    # Try to retrieve cache with naive datetime
    # The method should handle this gracefully by treating it as UTC
    cached_data = await cache_manager.get_database_data(db, str(test_user.id), database_id)

    # Should return the data (not None) since it's not expired
    assert cached_data is not None
    assert cached_data == data


@pytest.mark.asyncio
async def test_get_database_data_handles_different_users(db: Session, test_user: User):
    """Test that get_database_data correctly isolates data by user."""
    database_id = "shared-db"

    # Create another user
    user2 = auth_service.register(db, "test2@example.com", "password456")

    # Cache data for first user
    data1 = {
        "pages": [{"id": "page-1", "title": "User 1 Page"}],
        "database": {"id": database_id, "title": "Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), database_id, data1)

    # Cache different data for second user
    data2 = {
        "pages": [{"id": "page-2", "title": "User 2 Page"}],
        "database": {"id": database_id, "title": "Database"}
    }
    await cache_manager.cache_database_data(db, str(user2.id), database_id, data2)

    # Retrieve data for each user
    cached_data1 = await cache_manager.get_database_data(db, str(test_user.id), database_id)
    cached_data2 = await cache_manager.get_database_data(db, str(user2.id), database_id)

    # Verify each user gets their own data
    assert cached_data1 == data1
    assert cached_data2 == data2
    assert cached_data1 != cached_data2


@pytest.mark.asyncio
async def test_get_all_cached_databases_returns_empty_dict_when_no_cache(db: Session, test_user: User):
    """Test that get_all_cached_databases returns empty dict when no cache exists."""
    # Try to retrieve all cached databases when none exist
    result = await cache_manager.get_all_cached_databases(db, str(test_user.id))

    assert result == {}
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_all_cached_databases_returns_all_valid_caches(db: Session, test_user: User):
    """Test that get_all_cached_databases returns all valid cached databases."""
    # Cache data for multiple databases
    db1_id = "db-1"
    db1_data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": db1_id, "title": "Database 1"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), db1_id, db1_data)

    db2_id = "db-2"
    db2_data = {
        "pages": [{"id": "page-2", "title": "Page 2"}],
        "database": {"id": db2_id, "title": "Database 2"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), db2_id, db2_data)

    db3_id = "db-3"
    db3_data = {
        "pages": [{"id": "page-3", "title": "Page 3"}],
        "database": {"id": db3_id, "title": "Database 3"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), db3_id, db3_data)

    # Retrieve all cached databases
    result = await cache_manager.get_all_cached_databases(db, str(test_user.id))

    # Verify all databases are returned
    assert len(result) == 3
    assert db1_id in result
    assert db2_id in result
    assert db3_id in result
    assert result[db1_id] == db1_data
    assert result[db2_id] == db2_data
    assert result[db3_id] == db3_data


@pytest.mark.asyncio
async def test_get_all_cached_databases_filters_expired_entries(db: Session, test_user: User):
    """Test that get_all_cached_databases filters out expired entries."""
    import uuid
    user_uuid = uuid.UUID(str(test_user.id))
    now = datetime.now(timezone.utc)

    # Create valid cache entry
    valid_db_id = "valid-db"
    valid_data = {
        "pages": [{"id": "page-1", "title": "Valid Page"}],
        "database": {"id": valid_db_id, "title": "Valid Database"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), valid_db_id, valid_data)

    # Create expired cache entry
    expired_db_id = "expired-db"
    expired_data = {
        "pages": [{"id": "page-2", "title": "Expired Page"}],
        "database": {"id": expired_db_id, "title": "Expired Database"}
    }
    expired_entry = CachedDatabaseData(
        user_id=user_uuid,
        database_id=expired_db_id,
        data=expired_data,
        cached_at=now - timedelta(hours=1),
        expires_at=now - timedelta(minutes=1)  # Expired 1 minute ago
    )
    db.add(expired_entry)
    db.commit()

    # Retrieve all cached databases
    result = await cache_manager.get_all_cached_databases(db, str(test_user.id))

    # Verify only valid entry is returned
    assert len(result) == 1
    assert valid_db_id in result
    assert expired_db_id not in result
    assert result[valid_db_id] == valid_data

    # Verify expired entry was deleted from database
    remaining_expired = db.query(CachedDatabaseData).filter(
        CachedDatabaseData.user_id == user_uuid,
        CachedDatabaseData.database_id == expired_db_id
    ).first()
    assert remaining_expired is None


@pytest.mark.asyncio
async def test_get_all_cached_databases_handles_mixed_valid_and_expired(db: Session, test_user: User):
    """Test that get_all_cached_databases correctly handles mix of valid and expired entries."""
    import uuid
    user_uuid = uuid.UUID(str(test_user.id))
    now = datetime.now(timezone.utc)

    # Create multiple valid entries
    valid_db1_id = "valid-db-1"
    valid_data1 = {
        "pages": [{"id": "page-1", "title": "Valid Page 1"}],
        "database": {"id": valid_db1_id, "title": "Valid Database 1"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), valid_db1_id, valid_data1)

    valid_db2_id = "valid-db-2"
    valid_data2 = {
        "pages": [{"id": "page-2", "title": "Valid Page 2"}],
        "database": {"id": valid_db2_id, "title": "Valid Database 2"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), valid_db2_id, valid_data2)

    # Create multiple expired entries
    expired_db1_id = "expired-db-1"
    expired_data1 = {
        "pages": [{"id": "page-3", "title": "Expired Page 1"}],
        "database": {"id": expired_db1_id, "title": "Expired Database 1"}
    }
    expired_entry1 = CachedDatabaseData(
        user_id=user_uuid,
        database_id=expired_db1_id,
        data=expired_data1,
        cached_at=now - timedelta(hours=2),
        expires_at=now - timedelta(minutes=30)
    )
    db.add(expired_entry1)

    expired_db2_id = "expired-db-2"
    expired_data2 = {
        "pages": [{"id": "page-4", "title": "Expired Page 2"}],
        "database": {"id": expired_db2_id, "title": "Expired Database 2"}
    }
    expired_entry2 = CachedDatabaseData(
        user_id=user_uuid,
        database_id=expired_db2_id,
        data=expired_data2,
        cached_at=now - timedelta(hours=1),
        expires_at=now - timedelta(minutes=5)
    )
    db.add(expired_entry2)
    db.commit()

    # Retrieve all cached databases
    result = await cache_manager.get_all_cached_databases(db, str(test_user.id))

    # Verify only valid entries are returned
    assert len(result) == 2
    assert valid_db1_id in result
    assert valid_db2_id in result
    assert expired_db1_id not in result
    assert expired_db2_id not in result
    assert result[valid_db1_id] == valid_data1
    assert result[valid_db2_id] == valid_data2


@pytest.mark.asyncio
async def test_get_all_cached_databases_isolates_by_user(db: Session, test_user: User):
    """Test that get_all_cached_databases correctly isolates data by user."""
    # Create another user
    user2 = auth_service.register(db, "test3@example.com", "password789")

    # Cache data for first user
    user1_db1_id = "user1-db-1"
    user1_data1 = {
        "pages": [{"id": "page-1", "title": "User 1 Page 1"}],
        "database": {"id": user1_db1_id, "title": "User 1 Database 1"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), user1_db1_id, user1_data1)

    user1_db2_id = "user1-db-2"
    user1_data2 = {
        "pages": [{"id": "page-2", "title": "User 1 Page 2"}],
        "database": {"id": user1_db2_id, "title": "User 1 Database 2"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), user1_db2_id, user1_data2)

    # Cache data for second user
    user2_db1_id = "user2-db-1"
    user2_data1 = {
        "pages": [{"id": "page-3", "title": "User 2 Page 1"}],
        "database": {"id": user2_db1_id, "title": "User 2 Database 1"}
    }
    await cache_manager.cache_database_data(db, str(user2.id), user2_db1_id, user2_data1)

    # Retrieve all cached databases for each user
    user1_result = await cache_manager.get_all_cached_databases(db, str(test_user.id))
    user2_result = await cache_manager.get_all_cached_databases(db, str(user2.id))

    # Verify each user gets only their own data
    assert len(user1_result) == 2
    assert user1_db1_id in user1_result
    assert user1_db2_id in user1_result
    assert user2_db1_id not in user1_result

    assert len(user2_result) == 1
    assert user2_db1_id in user2_result
    assert user1_db1_id not in user2_result
    assert user1_db2_id not in user2_result


@pytest.mark.asyncio
async def test_get_all_cached_databases_uses_timezone_aware_comparison(db: Session, test_user: User):
    """Test that get_all_cached_databases uses timezone-aware datetime for expiration check."""
    # Cache some data
    db1_id = "db-timezone-1"
    db1_data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": db1_id, "title": "Database 1"}
    }
    await cache_manager.cache_database_data(db, str(test_user.id), db1_id, db1_data)

    # The method should use timezone-aware datetime for comparison
    # We can't verify this directly with SQLite, but we can verify the method
    # doesn't raise a TypeError about comparing naive and aware datetimes
    try:
        result = await cache_manager.get_all_cached_databases(db, str(test_user.id))
        # If we get here, the method successfully used timezone-aware comparison
        success = True
    except TypeError as e:
        if "can't compare offset-naive and offset-aware datetimes" in str(e):
            success = False
        else:
            raise

    assert success, "Method should use timezone-aware datetime for comparison"
    assert len(result) == 1
    assert db1_id in result


@pytest.mark.asyncio
async def test_get_all_cached_databases_handles_backward_compatibility(db: Session, test_user: User):
    """Test that get_all_cached_databases handles timezone-naive expires_at for backward compatibility."""
    import uuid
    user_uuid = uuid.UUID(str(test_user.id))
    now_naive = datetime.utcnow()  # Timezone-naive

    # Create cache entries with timezone-naive datetime (simulating old data)
    db1_id = "backward-compat-db-1"
    db1_data = {
        "pages": [{"id": "page-1", "title": "Page 1"}],
        "database": {"id": db1_id, "title": "Database 1"}
    }
    entry1 = CachedDatabaseData(
        user_id=user_uuid,
        database_id=db1_id,
        data=db1_data,
        cached_at=now_naive,
        expires_at=now_naive + timedelta(minutes=30)  # Still valid
    )
    db.add(entry1)

    db2_id = "backward-compat-db-2"
    db2_data = {
        "pages": [{"id": "page-2", "title": "Page 2"}],
        "database": {"id": db2_id, "title": "Database 2"}
    }
    entry2 = CachedDatabaseData(
        user_id=user_uuid,
        database_id=db2_id,
        data=db2_data,
        cached_at=now_naive,
        expires_at=now_naive + timedelta(minutes=20)  # Still valid
    )
    db.add(entry2)
    db.commit()

    # Try to retrieve all cached databases with naive datetime
    # The method should handle this gracefully by treating them as UTC
    result = await cache_manager.get_all_cached_databases(db, str(test_user.id))

    # Should return both entries (not empty) since they're not expired
    assert len(result) == 2
    assert db1_id in result
    assert db2_id in result
    assert result[db1_id] == db1_data
    assert result[db2_id] == db2_data
