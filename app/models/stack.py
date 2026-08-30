from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow


class Stack(Base):
    __tablename__ = "stack"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    picture = Column(String, nullable=False)
    order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project_stacks = relationship("ProjectStack", back_populates="stack")
