import uuid
import secrets
from datetime import datetime, timezone


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_slug() -> str:
    return secrets.token_hex(16)  # 32 caractères hexadécimaux, imprévisible
