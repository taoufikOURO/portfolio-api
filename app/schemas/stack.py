from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class StackBase(BaseModel):
    name: str
    picture: str
    order: int = 0


class StackCreate(StackBase):
    pass


class StackUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
    order: Optional[int] = None


class StackOut(StackBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = (
            True  # permet de créer ce schéma directement depuis un objet SQLAlchemy
        )
