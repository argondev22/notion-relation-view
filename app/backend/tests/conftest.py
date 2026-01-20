"""
Shared test configuration and fixtures for all tests.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base


# Create a single in-memory SQLite database that persists across connections
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use StaticPool to share the same connection
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create all tables at module load time
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clear all data from database tables before each test."""
    from app.models.user import User
    from app.models.notion_token import NotionToken
    from app.models.view import View

    db = TestingSessionLocal()
    try:
        # Delete in correct order (respecting foreign keys)
        db.query(NotionToken).delete()
        db.query(View).delete()
        db.query(User).delete()
        db.commit()
    except Exception:
        # If tables don't exist yet, just pass
        db.rollback()
    finally:
        db.close()
    yield


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


