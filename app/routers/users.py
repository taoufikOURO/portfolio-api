from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserProfileOut
from app.routers.auth import get_current_user
from app.core.storage import upload_image

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=UserProfileOut)
def get_profile(db: DBSession = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return user


@router.put("/", response_model=UserProfileOut)
async def update_profile(
    nom: Optional[str] = Form(None),
    prenom: Optional[str] = Form(None),
    titre_professionnel: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    a_propos: Optional[str] = Form(None),
    github: Optional[str] = Form(None),
    linkedin: Optional[str] = Form(None),
    cv: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: DBSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if nom is not None:
        current_user.nom = nom
    if prenom is not None:
        current_user.prenom = prenom
    if titre_professionnel is not None:
        current_user.titre_professionnel = titre_professionnel
    if bio is not None:
        current_user.bio = bio
    if a_propos is not None:
        current_user.a_propos = a_propos
    if github is not None:
        current_user.github = github
    if linkedin is not None:
        current_user.linkedin = linkedin
    if cv is not None:
        current_user.cv = cv

    if photo is not None:
        current_user.photo = upload_image(await photo.read(), photo.filename, "profile")

    db.commit()
    db.refresh(current_user)
    return current_user
