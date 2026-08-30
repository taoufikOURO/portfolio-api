from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.stack import StackOut

# ---------- PROJECT CONTRIBUTOR ----------


class ProjectContributorBase(BaseModel):
    name: str
    github_url: str


class ProjectContributorCreate(ProjectContributorBase):
    pass


class ProjectContributorOut(ProjectContributorBase):
    id: str

    class Config:
        from_attributes = True


# ---------- PROJECT ----------


class ProjectBase(BaseModel):
    name: str
    description: str
    app_link: Optional[str] = None
    github_link: Optional[str] = None
    picture: str
    order: int = 0


class ProjectCreate(ProjectBase):
    stack_ids: list[str] = []
    contributors: list[ProjectContributorCreate] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    app_link: Optional[str] = None
    github_link: Optional[str] = None
    picture: Optional[str] = None
    order: Optional[int] = None
    stack_ids: Optional[list[str]] = None
    contributors: Optional[list[ProjectContributorCreate]] = None


class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    contributors: list[ProjectContributorOut] = []
    stacks: list[StackOut] = []

    class Config:
        from_attributes = True
