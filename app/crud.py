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


def create_endpoint(db: Session, payload: schemas.EndpointCreate, *, user_id: int) -> models.Endpoint:
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
        user_id=user_id,
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


def get_endpoint(db: Session, endpoint_id: int, *, user_id: Optional[int] = None) -> Optional[models.Endpoint]:
    query = db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id)
    if user_id is not None:
        query = query.filter(models.Endpoint.user_id == user_id)
    return query.first()


def get_all_endpoints(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    *,
    user_id: Optional[int] = None,
) -> list[models.Endpoint]:
    query = db.query(models.Endpoint)
    if user_id is not None:
        query = query.filter(models.Endpoint.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def delete_endpoint(db: Session, endpoint_id: int, *, user_id: int) -> bool:
    endpoint = get_endpoint(db, endpoint_id, user_id=user_id)
    if not endpoint:
        return False
    db.delete(endpoint)
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


def get_all_logs(
    db: Session,
    skip: int = 0,
    limit: int = 200,
    *,
    user_id: Optional[int] = None,
) -> list[models.CheckLog]:
    query = db.query(models.CheckLog)
    if user_id is not None:
        query = query.join(models.Endpoint).filter(models.Endpoint.user_id == user_id)

    return (
        query.order_by(models.CheckLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_logs_for_endpoint(
    db: Session,
    endpoint_id: int,
    skip: int = 0,
    limit: int = 100,
    *,
    user_id: Optional[int] = None,
) -> list[models.CheckLog]:
    query = db.query(models.CheckLog).filter(models.CheckLog.endpoint_id == endpoint_id)
    if user_id is not None:
        query = query.join(models.Endpoint).filter(models.Endpoint.user_id == user_id)

    return (
        query.order_by(models.CheckLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_all_endpoints(db: Session, *, user_id: int) -> None:
    """Delete all endpoints for a user.

    Note: We intentionally do not reset the global sequence.
    """
    db.query(models.Endpoint).filter(models.Endpoint.user_id == user_id).delete()
    db.commit()


def update_endpoint_interval(
    db: Session,
    endpoint_id: int,
    interval_seconds: Optional[int] = None,
    interval_minutes: Optional[int] = None,
    *,
    user_id: Optional[int] = None,
) -> Optional[models.Endpoint]:
    """Update the check interval for an endpoint.

    Prefer interval_seconds; interval_minutes is accepted for older clients.
    Passing both as None disables auto-checks.
    """
    endpoint = get_endpoint(db, endpoint_id, user_id=user_id)
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
