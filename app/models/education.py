from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid, utcnow


class Education(Base):
    __tablename__ = "education"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)

    school_name = Column(String, nullable=False)
    school_address = Column(String, nullable=False)
    average = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    skills = relationship(
        "SkillOnEducation", back_populates="education", cascade="all, delete-orphan"
    )

    @property
    def skills_list(self):
        return [se.skill for se in self.skills]


class SkillOnEducation(Base):
    __tablename__ = "skill_on_education"

    education_id = Column(String, ForeignKey("education.id"), primary_key=True)
    skill_id = Column(String, ForeignKey("skill.id"), primary_key=True)

    education = relationship("Education", back_populates="skills")
    skill = relationship("Skill", back_populates="educations")
