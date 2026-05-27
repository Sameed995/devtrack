"""
Background scheduler for automatic health checks at regular intervals.
Uses APScheduler to manage periodic jobs.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import crud, models
from app.services.monitor import run_health_check


scheduler = BackgroundScheduler()
scheduled_jobs = {}  # Track which endpoints have scheduled jobs


def schedule_endpoint_check(endpoint: models.Endpoint) -> None:
    """Schedule automatic health checks for an endpoint if interval is set."""
    if not endpoint.interval_minutes:
        # Remove job if interval is None
        remove_endpoint_check(endpoint.id)
        return
    
    job_id = f"endpoint_{endpoint.id}"
    
    # Remove existing job if present
    if job_id in scheduled_jobs:
        scheduler.remove_job(job_id)
    
    # Schedule new job
    scheduler.add_job(
        func=run_scheduled_check,
        trigger=IntervalTrigger(minutes=endpoint.interval_minutes),
        id=job_id,
        args=[endpoint.id],
        replace_existing=True,
    )
    scheduled_jobs[job_id] = True


def remove_endpoint_check(endpoint_id: int) -> None:
    """Remove scheduled checks for an endpoint."""
    job_id = f"endpoint_{endpoint_id}"
    if job_id in scheduled_jobs:
        scheduler.remove_job(job_id)
        del scheduled_jobs[job_id]


def run_scheduled_check(endpoint_id: int) -> None:
    """Background task to run health check for an endpoint."""
    db = SessionLocal()
    try:
        endpoint = crud.get_endpoint(db, endpoint_id)
        if endpoint:
            run_health_check(db, endpoint)
    finally:
        db.close()


def reschedule_all_endpoints() -> None:
    """Load all endpoints from database and reschedule their checks."""
    db = SessionLocal()
    try:
        endpoints = crud.get_all_endpoints(db, limit=10_000)
        for endpoint in endpoints:
            schedule_endpoint_check(endpoint)
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.start()
        reschedule_all_endpoints()


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
