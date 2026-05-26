from typing import Optional
from sqlalchemy.orm import Session

from app import models, schemas


def create_endpoint(db: Session, payload: schemas.EndpointCreate) -> models.Endpoint:
    endpoint = models.Endpoint(
        name=payload.name,
        url=str(payload.url),
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


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
