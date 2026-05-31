from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
import re

_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False

def validate_password(password: str) -> None:

    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")

    if not re.search(r"\d", password):
        errors.append("one number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("one special character")

    if errors:
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain: "
                + ", ".join(errors)
            ),
        )


def _jwt_secret() -> str:
    # For local/dev convenience we fall back to a predictable secret.
    # In production you should always set JWT_SECRET.
    return os.getenv("JWT_SECRET", "devtrack-dev-secret-change-me")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _access_token_minutes() -> int:
    raw = os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60")
    try:
        return int(raw)
    except ValueError:
        return 60


def create_access_token(*, user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=_access_token_minutes())

    payload: dict[str, Any] = {
        "sub": username,
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": exp,
    }

    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> models.User:
    if credentials is None or not credentials.credentials:
        raise _unauthorized()

    token = credentials.credentials

    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except JWTError:
        raise _unauthorized("Invalid token")

    user_id = payload.get("uid")
    if not isinstance(user_id, int):
        # jose can decode JSON numbers as int; if it's missing/invalid, reject.
        raise _unauthorized("Invalid token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise _unauthorized("Invalid token")

    return user
