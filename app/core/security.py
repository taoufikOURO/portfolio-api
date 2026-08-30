"""Security utilities for password hashing, OTP generation, and session token management."""

import os
import random
import smtplib
import secrets
from email.mime.text import MIMEText
from datetime import timedelta
from passlib.context import CryptContext
from app.core.utils import utcnow

# ---------- MOTS DE PASSE ----------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- OTP ----------


def generate_otp_code() -> str:
    # code à 6 chiffres, ex: "042817"
    return f"{random.randint(0, 999999):06d}"


def otp_expiry():
    minutes = int(os.getenv("OTP_DURATION_MINUTES", "3"))
    return utcnow() + timedelta(minutes=minutes)


def send_otp_email(to_email: str, code: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    message = MIMEText(
        f"Ton code de connexion est : {code}\n\nIl expire dans {os.getenv('OTP_DURATION_MINUTES', "3")} minutes."
    )
    message["Subject"] = "Code de connexion - Portfolio Admin"
    message["From"] = smtp_user
    message["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()  # chiffre la connexion avant d'envoyer les identifiants
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, message.as_string())


# ---------- SESSION TOKEN ----------


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry():
    hours = int(os.getenv("SESSION_DURATION_HOURS", "24"))
    return utcnow() + timedelta(hours=hours)
