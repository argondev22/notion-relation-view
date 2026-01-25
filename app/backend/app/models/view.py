from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import json
from app.database import Base


class StringArray(TypeDecorator):
    """Custom type that uses ARRAY for PostgreSQL and JSON for SQLite"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        else:
            return json.dumps(value) if value is not None else '[]'

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        else:
            return json.loads(value) if value else []


class View(Base):
    __tablename__ = "views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    database_ids = Column(StringArray, nullable=False, default=list)
    zoom_level = Column(Float, default=1.0)
    pan_x = Column(Float, default=0.0)
    pan_y = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="views")
