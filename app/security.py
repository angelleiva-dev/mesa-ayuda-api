from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def crear_token(sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": sub, "exp": exp}, settings.secret_key, algorithm=settings.algorithm)


def leer_token(token: str) -> str | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]).get("sub")
    except jwt.PyJWTError:
        return None
