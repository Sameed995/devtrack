from typing import Optional
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    user = models.User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("Username already taken")


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_endpoint(db: Session, payload: schemas.EndpointCreate) -> models.Endpoint:
    interval_seconds: Optional[int]
    if payload.interval_seconds is not None:
        interval_seconds = payload.interval_seconds
    elif payload.interval_minutes is not None:
        interval_seconds = payload.interval_minutes * 60
    else:
        interval_seconds = None

    interval_minutes: Optional[int] = None
    if interval_seconds is not None and interval_seconds % 60 == 0 and interval_seconds >= 60:
        interval_minutes = interval_seconds // 60

    endpoint = models.Endpoint(
        name=payload.name,
        url=str(payload.url),
        interval_seconds=interval_seconds,
        interval_minutes=interval_minutes,
    )
    try:
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)
        return endpoint
    except IntegrityError:
        db.rollback()
        raise ValueError("An endpoint with this URL already exists")


def get_endpoint(db: Session, endpoint_id: int) -> Optional[models.Endpoint]:
    return db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()


def get_all_endpoints(db: Session, skip: int = 0, limit: int = 100) -> list[models.Endpoint]:
    return db.query(models.Endpoint).offset(skip).limit(limit).all()


def delete_endpoint(db: Session, endpoint_id: int) -> bool:
    endpoint = get_endpoint(db, endpoint_id)
    if not endpoint:
        return False
    db.delete(endpoint)
    db.commit()
    
    # If no endpoints left, reset the sequence
    remaining_count = db.query(models.Endpoint).count()
    if remaining_count == 0:
        db.execute(text("ALTER SEQUENCE public.endpoints_id_seq RESTART WITH 1"))
        db.commit()
    
    return True


def create_check_log(
    db: Session,
    endpoint_id: int,
    status: models.StatusEnum,
    response_time_ms: Optional[float],
    status_code: Optional[int],
    error_message: Optional[str],
) -> models.CheckLog:
    log = models.CheckLog(
        endpoint_id=endpoint_id,
        status=status,
        response_time_ms=response_time_ms,
        status_code=status_code,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_all_logs(db: Session, skip: int = 0, limit: int = 200) -> list[models.CheckLog]:
    return (
        db.query(models.CheckLog)
        .order_by(models.CheckLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_logs_for_endpoint(
    db: Session, endpoint_id: int, skip: int = 0, limit: int = 100
) -> list[models.CheckLog]:
    return (
        db.query(models.CheckLog)
        .filter(models.CheckLog.endpoint_id == endpoint_id)
        .order_by(models.CheckLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_all_endpoints(db: Session) -> None:
    """Delete all endpoints and reset the PostgreSQL sequence to 1."""
    db.query(models.Endpoint).delete()
    db.execute(text("ALTER SEQUENCE public.endpoints_id_seq RESTART WITH 1"))
    db.commit()


def update_endpoint_interval(
    db: Session,
    endpoint_id: int,
    interval_seconds: Optional[int] = None,
    interval_minutes: Optional[int] = None,
) -> Optional[models.Endpoint]:
    """Update the check interval for an endpoint.

    Prefer interval_seconds; interval_minutes is accepted for older clients.
    Passing both as None disables auto-checks.
    """
    endpoint = get_endpoint(db, endpoint_id)
    if not endpoint:
        return None

    if interval_seconds is None and interval_minutes is not None:
        interval_seconds = interval_minutes * 60

    endpoint.interval_seconds = interval_seconds
    if interval_seconds is not None and interval_seconds % 60 == 0 and interval_seconds >= 60:
        endpoint.interval_minutes = interval_seconds // 60
    else:
        endpoint.interval_minutes = None

    db.commit()
    db.refresh(endpoint)
    return endpoint
