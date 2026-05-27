from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class StatusEnum(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    interval_minutes = Column(Integer, nullable=True)  # 2, 5, 10, 15 minutes (None = manual only)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    logs = relationship("CheckLog", back_populates="endpoint", cascade="all, delete-orphan")


class CheckLog(Base):
    __tablename__ = "check_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SAEnum(StatusEnum), nullable=False)
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    endpoint = relationship("Endpoint", back_populates="logs")
