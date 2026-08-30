from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.skill import SkillOut


class EducationBase(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    school_name: str
    school_address: str
    average: Optional[float] = None


class EducationCreate(EducationBase):
    skill_ids: list[str] = []


class EducationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    school_name: Optional[str] = None
    school_address: Optional[str] = None
    average: Optional[float] = None
    skill_ids: Optional[list[str]] = None


class EducationOut(EducationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    skills: list[SkillOut] = Field(default=[], alias="skills_list")

    class Config:
        from_attributes = True
        populate_by_name = True
