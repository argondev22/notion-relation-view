from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import json
from app.database import Base


class View(Base):
    __tablename__ = "views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    # Use Text for SQLite compatibility, store as JSON string
    _database_ids = Column("database_ids", Text, nullable=False)
    zoom_level = Column(Float, default=1.0)
    pan_x = Column(Float, default=0.0)
    pan_y = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="views")

    @property
    def database_ids(self):
        """Get database_ids as a list."""
        if self._database_ids:
            return json.loads(self._database_ids)
        return []

    @database_ids.setter
    def database_ids(self, value):
        """Set database_ids from a list."""
        if isinstance(value, list):
            self._database_ids = json.dumps(value)
        elif isinstance(value, str):
            # Already a JSON string
            self._database_ids = value
        else:
            self._database_ids = json.dumps([])
