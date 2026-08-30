from sqlalchemy import (
    Column,
    String,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.utils import generate_uuid


class Skill(Base):
    __tablename__ = "skill"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)

    educations = relationship("SkillOnEducation", back_populates="skill")
    experiences = relationship("ExperienceSkill", back_populates="skill")
