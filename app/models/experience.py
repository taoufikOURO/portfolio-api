from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow


class Experience(Base):
    __tablename__ = "experience"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)

    company_name = Column(String, nullable=False)
    company_address = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    skills = relationship(
        "ExperienceSkill", back_populates="experience", cascade="all, delete-orphan"
    )

    @property
    def skills_list(self):
        return [es.skill for es in self.skills]


class ExperienceSkill(Base):
    __tablename__ = "experience_skill"

    experience_id = Column(String, ForeignKey("experience.id"), primary_key=True)
    skill_id = Column(String, ForeignKey("skill.id"), primary_key=True)

    experience = relationship("Experience", back_populates="skills")
    skill = relationship("Skill", back_populates="experiences")
