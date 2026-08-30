"""Articles API routes."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut
from app.routers.auth import get_current_user
from app.core.storage import upload_image

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=list[ArticleOut])
def list_articles(db: DBSession = Depends(get_db), published_only: bool = True):
    query = db.query(Article)
    if published_only:
        query = query.filter(Article.published == True)
    return query.order_by(Article.created_at.desc()).all()


@router.get("/{slug}", response_model=ArticleOut)
def get_article(slug: str, db: DBSession = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


@router.post("/upload", response_model=ArticleOut, status_code=201)
async def upload_article(
    title: str = Form(...),
    excerpt: str = Form(...),
    published: bool = Form(False),
    file: UploadFile = File(...),
    cover_image: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not file.filename.endswith(".md"):
        raise HTTPException(
            status_code=400, detail="Seuls les fichiers .md sont acceptés"
        )

    content = (await file.read()).decode("utf-8")

    cover_url = None
    if cover_image is not None:
        cover_url = upload_image(
            await cover_image.read(), cover_image.filename, "articles"
        )

    article = Article(
        title=title,
        excerpt=excerpt,
        content=content,
        cover_image=cover_url,
        published=published,
        published_at=datetime.now(timezone.utc) if published else None,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.put("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: str,
    title: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    published: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    cover_image: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")

    was_published = article.published

    if title is not None:
        article.title = title
    if excerpt is not None:
        article.excerpt = excerpt
    if published is not None:
        article.published = published

    if file is not None:
        if not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400, detail="Seuls les fichiers .md sont acceptés"
            )
        article.content = (await file.read()).decode("utf-8")

    if cover_image is not None:
        article.cover_image = upload_image(
            await cover_image.read(), cover_image.filename, "articles"
        )

    if not was_published and article.published:
        article.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=204)
def delete_article(
    article_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    db.delete(article)
    db.commit()
    return None
