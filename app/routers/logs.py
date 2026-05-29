from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["Logs"], dependencies=[Depends(get_current_user)])


@router.get("/logs", response_model=list[schemas.CheckLogResponse])
def get_all_logs(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    """Return all check logs across every endpoint, ordered by most recent first."""
    return crud.get_all_logs(db, skip=skip, limit=limit)


@router.get("/endpoints/{endpoint_id}/logs", response_model=list[schemas.CheckLogResponse])
def get_logs_for_endpoint(
    endpoint_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return check logs for a specific endpoint, ordered by most recent first."""
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")

    return crud.get_logs_for_endpoint(db, endpoint_id=endpoint_id, skip=skip, limit=limit)
