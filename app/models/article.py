from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
)
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow, generate_slug


class Article(Base):
    __tablename__ = "article"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, default=generate_slug)
    excerpt = Column(String, nullable=False)
    content = Column(
        Text, nullable=False
    )  # Markdown brut extrait du fichier .md uploadé
    cover_image = Column(String, nullable=True)

    published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
