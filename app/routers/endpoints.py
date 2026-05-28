from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.services.monitor import run_health_check, compute_summary
from app.services.scheduler import schedule_endpoint_check

router = APIRouter(prefix="/endpoints", tags=["Endpoints"])


@router.post("/", response_model=schemas.EndpointResponse, status_code=status.HTTP_201_CREATED)
def create_endpoint(payload: schemas.EndpointCreate, db: Session = Depends(get_db)):
    """Register a new API endpoint to monitor."""
    try:
        endpoint = crud.create_endpoint(db, payload)
        # Schedule automatic checks if interval is set
        schedule_endpoint_check(endpoint)
        return endpoint
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[schemas.EndpointResponse])
def list_endpoints(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return all registered endpoints."""
    return crud.get_all_endpoints(db, skip=skip, limit=limit)


@router.get("/{endpoint_id}", response_model=schemas.EndpointResponse)
def get_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Fetch a single endpoint by ID."""
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
    return endpoint


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Delete an endpoint and all its associated check logs."""
    deleted = crud.delete_endpoint(db, endpoint_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_endpoints(db: Session = Depends(get_db)):
    """Delete all endpoints and reset the ID sequence to 1."""
    crud.delete_all_endpoints(db)


@router.post("/{endpoint_id}/check", response_model=schemas.CheckLogResponse, status_code=status.HTTP_201_CREATED)
def trigger_check(endpoint_id: int, db: Session = Depends(get_db)):
    """
    Manually trigger a health check for a registered endpoint.
    Fires an HTTP GET, measures response time, and stores the result.
    """
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")

    log = run_health_check(db, endpoint)
    return log


@router.get("/{endpoint_id}/summary", response_model=schemas.EndpointSummary)
def get_summary(endpoint_id: int, db: Session = Depends(get_db)):
    """
    Return uptime percentage and average response time
    for a given endpoint based on all stored check logs.
    """
    endpoint = crud.get_endpoint(db, endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")

    return compute_summary(db, endpoint)


@router.patch("/{endpoint_id}/interval", response_model=schemas.EndpointResponse)
def update_endpoint_interval(endpoint_id: int, payload: schemas.EndpointUpdate, db: Session = Depends(get_db)):
    """Update the automatic check interval for an endpoint."""
    endpoint = crud.update_endpoint_interval(
        db,
        endpoint_id,
        interval_seconds=payload.interval_seconds,
        interval_minutes=payload.interval_minutes,
    )
    if not endpoint:
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
    
    # Reschedule checks with new interval
    schedule_endpoint_check(endpoint)
    return endpoint
