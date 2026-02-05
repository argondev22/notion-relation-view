"""
View Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class View(Base):
    """View model for storing user view configurations"""

    __tablename__ = "views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    database_ids = Column(ARRAY(String), nullable=False)
    zoom_level = Column(Float, default=1.0, nullable=False)
    pan_x = Column(Float, default=0.0, nullable=False)
    pan_y = Column(Float, default=0.0, nullable=False)
    extraction_mode = Column(String(20), default="property", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="views")

    def __repr__(self):
        return f"<View(id={self.id}, name={self.name}, user_id={self.user_id})>"
