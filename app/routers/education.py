from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.education import Education, SkillOnEducation
from app.models.skill import Skill
from app.schemas.education import EducationOut, EducationCreate, EducationUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/education", tags=["education"])


@router.get("/", response_model=list[EducationOut])
def list_education(db: DBSession = Depends(get_db)):
    return db.query(Education).order_by(Education.start_date.desc()).all()


@router.get("/{education_id}", response_model=EducationOut)
def get_education(education_id: str, db: DBSession = Depends(get_db)):
    edu = db.query(Education).filter(Education.id == education_id).first()
    if not edu:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    return edu


@router.post("/", response_model=EducationOut, status_code=201)
def create_education(
    payload: EducationCreate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = payload.model_dump(exclude={"skill_ids"})
    edu = Education(**data)
    db.add(edu)
    db.flush()

    if payload.skill_ids:
        skills = db.query(Skill).filter(Skill.id.in_(payload.skill_ids)).all()
        if len(skills) != len(payload.skill_ids):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs compétences sont introuvables"
            )
        edu.skills = [
            SkillOnEducation(skill_id=s.id, education_id=edu.id) for s in skills
        ]

    db.commit()
    db.refresh(edu)
    return edu


@router.put("/{education_id}", response_model=EducationOut)
def update_education(
    education_id: str,
    payload: EducationUpdate,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    edu = db.query(Education).filter(Education.id == education_id).first()
    if not edu:
        raise HTTPException(status_code=404, detail="Formation introuvable")

    update_data = payload.model_dump(exclude_unset=True, exclude={"skill_ids"})
    for field, value in update_data.items():
        setattr(edu, field, value)

    if payload.skill_ids is not None:
        skills = db.query(Skill).filter(Skill.id.in_(payload.skill_ids)).all()
        if len(skills) != len(payload.skill_ids):
            raise HTTPException(
                status_code=400, detail="Une ou plusieurs compétences sont introuvables"
            )
        edu.skills = [
            SkillOnEducation(skill_id=s.id, education_id=edu.id) for s in skills
        ]

    db.commit()
    db.refresh(edu)
    return edu


@router.delete("/{education_id}", status_code=204)
def delete_education(
    education_id: str,
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    edu = db.query(Education).filter(Education.id == education_id).first()
    if not edu:
        raise HTTPException(status_code=404, detail="Formation introuvable")
    db.delete(edu)
    db.commit()
    return None
