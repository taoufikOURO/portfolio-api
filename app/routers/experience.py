"""Experience API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.experience import Experience, ExperienceSkill
from app.models.skill import Skill
from app.schemas.experience import ExperienceOut, ExperienceCreate, ExperienceUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/experience", tags=["experience"])


@router.get("/", response_model=list[ExperienceOut])
def list_experience(db: DBSession = Depends(get_db)):
    return db.query(Experience).order_by(Experience.start_date.desc()).all()


@router.get("/{experience_id}", response_model=ExperienceOut)
def get_experience(experience_id: str, db: DBSession = Depends(get_db)):
    exp = db.query(Experience).filter(Experience.id == experience_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expérience introuvable")
    return exp


@router.post("/", response_model=ExperienceOut, status_code=201)
def create_experience(
    payload: ExperienceCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = payload.model_dump(exclude={"skill_ids"})
    exp = Experience(**data)
    db.add(exp)
    db.flush()

    if payload.skill_ids:
        skills = db.query(Skill).filter(Skill.id.in_(payload.skill_ids)).all()
        if len(skills) != len(payload.skill_ids):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs compétences sont introuvables"
            )
        exp.skills = [
            ExperienceSkill(skill_id=s.id, experience_id=exp.id) for s in skills
        ]

    db.commit()
    db.refresh(exp)
    return exp


@router.put("/{experience_id}", response_model=ExperienceOut)
def update_experience(
    experience_id: str,
    payload: ExperienceUpdate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    exp = db.query(Experience).filter(Experience.id == experience_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expérience introuvable")

    update_data = payload.model_dump(exclude_unset=True, exclude={"skill_ids"})
    for field, value in update_data.items():
        setattr(exp, field, value)

    if payload.skill_ids is not None:
        skills = db.query(Skill).filter(Skill.id.in_(payload.skill_ids)).all()
        if len(skills) != len(payload.skill_ids):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs compétences sont introuvables"
            )
        exp.skills = [
            ExperienceSkill(skill_id=s.id, experience_id=exp.id) for s in skills
        ]

    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/{experience_id}", status_code=204)
def delete_experience(
    experience_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    exp = db.query(Experience).filter(Experience.id == experience_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expérience introuvable")
    db.delete(exp)
    db.commit()
    return None
