from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.skill import SkillOut


class ExperienceBase(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    company_name: str
    company_address: str


class ExperienceCreate(ExperienceBase):
    skill_ids: list[str] = []


class ExperienceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    skill_ids: Optional[list[str]] = None


class ExperienceOut(ExperienceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    skills: list[SkillOut] = Field(default=[], alias="skills_list")

    class Config:
        from_attributes = True
        populate_by_name = True
