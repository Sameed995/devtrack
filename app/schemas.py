from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, ConfigDict

from app.models import StatusEnum


class EndpointCreate(BaseModel):
    name: str
    url: HttpUrl


class EndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    created_at: datetime


class CheckLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint_id: int
    status: StatusEnum
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime


class EndpointSummary(BaseModel):
    endpoint_id: int
    endpoint_name: str
    total_checks: int
    up_count: int
    down_count: int
    uptime_percentage: float
    average_response_time_ms: Optional[float] = None
    last_checked_at: Optional[datetime] = None
