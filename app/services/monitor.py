import time
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app import crud, models


# Timeout for outbound HTTP health checks (seconds)
REQUEST_TIMEOUT = 10


def run_health_check(db: Session, endpoint: models.Endpoint) -> models.CheckLog:
    """
    Fire an HTTP GET to the endpoint URL, measure response time,
    classify the result as UP or DOWN, and persist a CheckLog.

    UP: HTTP response with 2xx status code.
    DOWN: Non-2xx response or any network/timeout exception.
    """
    status: models.StatusEnum
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None

    start = time.perf_counter()

    try:
        response = requests.get(endpoint.url, timeout=REQUEST_TIMEOUT)
        elapsed = time.perf_counter() - start
        response_time_ms = round(elapsed * 1000, 2)
        status_code = response.status_code

        if 200 <= status_code <= 299:
            status = models.StatusEnum.UP
        else:
            status = models.StatusEnum.DOWN
            error_message = f"Received non-2xx status code: {status_code}"

    except requests.exceptions.Timeout:
        elapsed = time.perf_counter() - start
        response_time_ms = round(elapsed * 1000, 2)
        status = models.StatusEnum.DOWN
        error_message = f"Request timed out after {REQUEST_TIMEOUT}s"

    except requests.exceptions.ConnectionError as exc:
        status = models.StatusEnum.DOWN
        error_message = f"Connection error: {str(exc)[:200]}"

    except requests.exceptions.RequestException as exc:
        status = models.StatusEnum.DOWN
        error_message = f"Request failed: {str(exc)[:200]}"

    log = crud.create_check_log(
        db=db,
        endpoint_id=endpoint.id,
        status=status,
        response_time_ms=response_time_ms,
        status_code=status_code,
        error_message=error_message,
    )
    return log


def compute_summary(db: Session, endpoint: models.Endpoint) -> dict:
    """
    Calculate uptime percentage and average response time
    over all recorded check logs for the given endpoint.
    """
    logs = crud.get_logs_for_endpoint(db, endpoint_id=endpoint.id, limit=10_000)

    total = len(logs)
    if total == 0:
        return {
            "endpoint_id": endpoint.id,
            "endpoint_name": endpoint.name,
            "total_checks": 0,
            "up_count": 0,
            "down_count": 0,
            "uptime_percentage": 0.0,
            "average_response_time_ms": None,
            "last_checked_at": None,
        }

    up_count = sum(1 for log in logs if log.status == models.StatusEnum.UP)
    down_count = total - up_count

    response_times = [log.response_time_ms for log in logs if log.response_time_ms is not None]
    avg_response_time = round(sum(response_times) / len(response_times), 2) if response_times else None

    return {
        "endpoint_id": endpoint.id,
        "endpoint_name": endpoint.name,
        "total_checks": total,
        "up_count": up_count,
        "down_count": down_count,
        "uptime_percentage": round((up_count / total) * 100, 2),
        "average_response_time_ms": avg_response_time,
        "last_checked_at": logs[0].created_at if logs else None,
    }
