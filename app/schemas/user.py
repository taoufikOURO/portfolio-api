from typing import Optional
from pydantic import BaseModel, EmailStr


class UserProfileOut(BaseModel):
    id: str
    email: EmailStr
    nom: str
    prenom: str
    titre_professionnel: Optional[str] = None
    bio: Optional[str] = None
    a_propos: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    photo: Optional[str] = None
    cv: Optional[str] = None

    class Config:
        from_attributes = True
        # note : password, otp_code, otp_expires_at sont VOLONTAIREMENT absents ici


class UserProfileUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    titre_professionnel: Optional[str] = None
    bio: Optional[str] = None
    a_propos: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    photo: Optional[str] = None
    cv: Optional[str] = None
