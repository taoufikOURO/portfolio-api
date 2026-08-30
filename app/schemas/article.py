from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArticleBase(BaseModel):
    title: str
    excerpt: str
    cover_image: Optional[str] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    published: Optional[bool] = None


class ArticleOut(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: str
    content: str
    cover_image: Optional[str] = None
    published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
