from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, ConfigDict, model_validator

from app.models import StatusEnum


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class EndpointCreate(BaseModel):
    name: str
    url: HttpUrl
    # Preferred: seconds (supports 10s)
    interval_seconds: Optional[int] = None  # 10, 120, 300, 600, 900 or None
    # Backward compatibility: minutes
    interval_minutes: Optional[int] = None  # 2, 5, 10, 15 or None

    @model_validator(mode="after")
    def validate_interval(self):
        allowed_seconds = {10, 120, 300, 600, 900}
        allowed_minutes = {2, 5, 10, 15}

        if self.interval_seconds is not None and self.interval_seconds not in allowed_seconds:
            raise ValueError("interval_seconds must be one of 10, 120, 300, 600, 900 or null")

        if self.interval_minutes is not None and self.interval_minutes not in allowed_minutes:
            raise ValueError("interval_minutes must be one of 2, 5, 10, 15 or null")

        if self.interval_seconds is not None and self.interval_minutes is not None:
            expected = self.interval_minutes * 60
            if self.interval_seconds != expected:
                raise ValueError("Provide only interval_seconds or interval_minutes (not both)")

        return self


class EndpointUpdate(BaseModel):
    interval_seconds: Optional[int] = None
    interval_minutes: Optional[int] = None

    @model_validator(mode="after")
    def validate_interval(self):
        allowed_seconds = {10, 120, 300, 600, 900}
        allowed_minutes = {2, 5, 10, 15}

        if self.interval_seconds is not None and self.interval_seconds not in allowed_seconds:
            raise ValueError("interval_seconds must be one of 10, 120, 300, 600, 900 or null")

        if self.interval_minutes is not None and self.interval_minutes not in allowed_minutes:
            raise ValueError("interval_minutes must be one of 2, 5, 10, 15 or null")

        if self.interval_seconds is not None and self.interval_minutes is not None:
            expected = self.interval_minutes * 60
            if self.interval_seconds != expected:
                raise ValueError("Provide only interval_seconds or interval_minutes (not both)")

        return self


class EndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    interval_seconds: Optional[int] = None
    interval_minutes: Optional[int] = None
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
