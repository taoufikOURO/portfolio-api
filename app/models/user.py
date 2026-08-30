from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    titre_professionnel = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    a_propos = Column(Text, nullable=True)

    github = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    cv = Column(String, nullable=True)

    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    __tablename__ = "session"

    id = Column(String, primary_key=True, default=generate_uuid)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="sessions")
