from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Enum as SAEnum,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class StatusEnum(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"


class Endpoint(Base):
    __tablename__ = "endpoints"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "url",
            name="uq_endpoints_user_url",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    display_id = Column(Integer, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name = Column(String(255), nullable=False)

    url = Column(String(2048), nullable=False)

    # Scheduling configuration
    # Prefer interval_seconds for new functionality
    # (supports sub-minute intervals)
    interval_minutes = Column(Integer, nullable=True)

    # 10, 120, 300, 600, 900
    # None = manual only
    interval_seconds = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    logs = relationship(
        "CheckLog",
        back_populates="endpoint",
        cascade="all, delete-orphan",
    )

    user = relationship(
        "User",
        back_populates="endpoints",
    )


class CheckLog(Base):
    __tablename__ = "check_logs"

    id = Column(Integer, primary_key=True, index=True)

    endpoint_id = Column(
        Integer,
        ForeignKey("endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        SAEnum(StatusEnum),
        nullable=False,
    )

    response_time_ms = Column(Float, nullable=True)

    status_code = Column(Integer, nullable=True)

    error_message = Column(String(1024), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    endpoint = relationship(
        "Endpoint",
        back_populates="logs",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    # OTP system
    otp_code = Column(
        String(6),
        nullable=True,
    )

    otp_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # email_verification / password_reset
    otp_purpose = Column(
        String(32),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    endpoints = relationship(
        "Endpoint",
        back_populates="user",
        cascade="all, delete-orphan",
    )