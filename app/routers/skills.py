"""Skill management endpoints for the FastAPI project."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillOut, SkillCreate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/", response_model=list[SkillOut])
def list_skills(db: DBSession = Depends(get_db)):
    return db.query(Skill).all()


@router.post("/", response_model=SkillOut, status_code=201)
def create_skill(
    payload: SkillCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    existing = db.query(Skill).filter(Skill.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette compétence existe déjà")
    skill = Skill(name=payload.name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=SkillOut)
def update_skill(
    skill_id: str,
    payload: SkillCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence introuvable")

    existing = (
        db.query(Skill).filter(Skill.name == payload.name, Skill.id != skill_id).first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Une autre compétence porte déjà ce nom"
        )

    skill.name = payload.name
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=204)
def delete_skill(
    skill_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Compétence introuvable")
    db.delete(skill)
    db.commit()
    return None
