"""Authentication module for the FastAPI application. Handles user login, OTP verification, and session management."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request, Cookie
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, EmailStr
import os

from app.core.database import get_db
from app.models.user import User, Session as SessionModel
from app.core.security import (
    verify_password,
    generate_otp_code,
    otp_expiry,
    send_otp_email,
    generate_session_token,
    session_expiry,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/login")
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    code = generate_otp_code()
    user.otp_code = code
    user.otp_expires_at = otp_expiry()
    db.commit()

    send_otp_email(user.email, code)

    return {"message": "Code OTP envoyé par email"}


@router.post("/verify-otp")
def verify_otp(
    payload: VerifyOtpRequest, response: Response, db: DBSession = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not user.otp_code:
        raise HTTPException(
            status_code=401, detail="Aucune demande de connexion en cours"
        )

    if user.otp_code != payload.code:
        raise HTTPException(status_code=401, detail="Code invalide")

    if user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Code expiré")

    # OTP consommé : on l'efface pour empêcher toute réutilisation
    user.otp_code = None
    user.otp_expires_at = None

    token = generate_session_token()
    session = SessionModel(token=token, user_id=user.id, expires_at=session_expiry())
    db.add(session)
    db.commit()

    response.set_cookie(
        key=os.getenv("SESSION_COOKIE_NAME", "session_token"),
        value=token,
        httponly=True,
        secure=True,  # à passer à False si tu testes en localhost sans HTTPS
        samesite="lax",
        max_age=int(os.getenv("SESSION_DURATION_HOURS", "24")) * 3600,
    )

    return {"message": "Connexion réussie"}


@router.post("/logout")
def logout(response: Response, request: Request, db: DBSession = Depends(get_db)):
    cookie_name = os.getenv("SESSION_COOKIE_NAME", "session_token")
    token = request.cookies.get(cookie_name)

    if token:
        db.query(SessionModel).filter(SessionModel.token == token).delete()
        db.commit()

    response.delete_cookie(cookie_name)
    return {"message": "Déconnecté"}


def get_current_user(
    request: Request,
    db: DBSession = Depends(get_db),
) -> User:
    cookie_name = os.getenv("SESSION_COOKIE_NAME", "session_token")
    token = request.cookies.get(cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    session = db.query(SessionModel).filter(SessionModel.token == token).first()

    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")

    return session.user
