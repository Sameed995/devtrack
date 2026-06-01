from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password
from app.services.email import generate_otp, send_otp_email, get_otp_expiry_time


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    """Create a new user and send OTP to email."""
    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        email_verified=False,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Generate OTP and send email
        otp_code = generate_otp()
        user.otp_code = otp_code
        user.otp_expires_at = get_otp_expiry_time()
        db.commit()
        db.refresh(user)
        
        # Send OTP email
        send_otp_email(user.email, otp_code)
        
        return user
    except IntegrityError as e:
        db.rollback()
        if 'username' in str(e):
            raise ValueError("Username already taken")
        elif 'email' in str(e):
            raise ValueError("Email already registered")
        raise


def verify_user_otp(db: Session, email: str, otp_code: str) -> Optional[models.User]:
    """Verify OTP and mark email as verified.
    
    Raises ValueError with specific error messages:
    - "Email not found"
    - "OTP has expired"
    - "Invalid OTP code"
    """
    user = get_user_by_email(db, email)
    if not user:
        raise ValueError("Email not found")
    
    # Check if OTP is expired
    if user.otp_expires_at and datetime.now(timezone.utc) > user.otp_expires_at:
        raise ValueError("OTP has expired")
    
    # Check if OTP matches
    if user.otp_code != otp_code:
        raise ValueError("Invalid OTP code")
    
    # Mark email as verified
    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    # Only allow login if email is verified
    if not user.email_verified:
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

    # Get latest display_id for this user
    last_endpoint = (
        db.query(models.Endpoint)
        .filter(models.Endpoint.user_id == user_id)
        .order_by(models.Endpoint.display_id.desc())
        .first()
    )

    next_display_id = 1 if not last_endpoint else last_endpoint.display_id + 1

    endpoint = models.Endpoint(
        user_id=user_id,
        display_id=next_display_id,
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
