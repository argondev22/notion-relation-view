"""
Tests for database models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.database import Base
from app.models import User, NotionToken, View


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_user_model_creation(db_session):
    """Test that User model can be created and saved"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    # Verify user was created
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password"
    assert user.created_at is not None
    assert user.updated_at is not None


def test_notion_token_model_creation(db_session):
    """Test that NotionToken model can be created and saved"""
    # Create a user first
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    # Create notion token
    token = NotionToken(
        user_id=user.id,
        encrypted_token="encrypted_token_value"
    )
    db_session.add(token)
    db_session.commit()

    # Verify token was created
    assert token.user_id == user.id
    assert token.encrypted_token == "encrypted_token_value"
    assert token.created_at is not None
    assert token.updated_at is not None


def test_view_model_creation(db_session):
    """Test that View model can be created and saved"""
    # Create a user first
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    # Create view
    view = View(
        user_id=user.id,
        name="Test View",
        database_ids=["db1", "db2"],
        zoom_level=1.5,
        pan_x=10.0,
        pan_y=20.0
    )
    db_session.add(view)
    db_session.commit()

    # Verify view was created
    assert view.id is not None
    assert view.user_id == user.id
    assert view.name == "Test View"
    assert view.database_ids == ["db1", "db2"]
    assert view.zoom_level == 1.5
    assert view.pan_x == 10.0
    assert view.pan_y == 20.0
    assert view.created_at is not None
    assert view.updated_at is not None


def test_user_notion_token_relationship(db_session):
    """Test the relationship between User and NotionToken"""
    # Create user with notion token
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    token = NotionToken(
        user_id=user.id,
        encrypted_token="encrypted_token_value"
    )
    db_session.add(token)
    db_session.commit()

    # Refresh to load relationships
    db_session.refresh(user)

    # Verify relationship
    assert user.notion_token is not None
    assert user.notion_token.encrypted_token == "encrypted_token_value"
    assert token.user.email == "test@example.com"


def test_user_views_relationship(db_session):
    """Test the relationship between User and Views"""
    # Create user with multiple views
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    view1 = View(
        user_id=user.id,
        name="View 1",
        database_ids=["db1"]
    )
    view2 = View(
        user_id=user.id,
        name="View 2",
        database_ids=["db2"]
    )
    db_session.add_all([view1, view2])
    db_session.commit()

    # Refresh to load relationships
    db_session.refresh(user)

    # Verify relationship
    assert len(user.views) == 2
    assert view1.user.email == "test@example.com"
    assert view2.user.email == "test@example.com"


def test_cascade_delete_notion_token(db_session):
    """Test that deleting a user cascades to notion_token"""
    # Create user with notion token
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    token = NotionToken(
        user_id=user.id,
        encrypted_token="encrypted_token_value"
    )
    db_session.add(token)
    db_session.commit()

    user_id = user.id

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify token was also deleted
    deleted_token = db_session.query(NotionToken).filter_by(user_id=user_id).first()
    assert deleted_token is None


def test_cascade_delete_views(db_session):
    """Test that deleting a user cascades to views"""
    # Create user with views
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    view = View(
        user_id=user.id,
        name="Test View",
        database_ids=["db1"]
    )
    db_session.add(view)
    db_session.commit()

    user_id = user.id

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify view was also deleted
    deleted_views = db_session.query(View).filter_by(user_id=user_id).all()
    assert len(deleted_views) == 0


def test_view_default_values(db_session):
    """Test that View model has correct default values"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()

    # Create view without optional fields
    view = View(
        user_id=user.id,
        name="Test View",
        database_ids=["db1"]
    )
    db_session.add(view)
    db_session.commit()

    # Verify default values
    assert view.zoom_level == 1.0
    assert view.pan_x == 0.0
    assert view.pan_y == 0.0
