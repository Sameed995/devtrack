import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
DEFAULT_SQLITE_URL = "sqlite:///./devtrack.db"


def _create_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def _build_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning("DATABASE_URL is not set; using local SQLite database at %s", DEFAULT_SQLITE_URL)
        return DEFAULT_SQLITE_URL, _create_engine(DEFAULT_SQLITE_URL)

    engine = _create_engine(database_url)

    try:
        with engine.connect():
            pass
        return database_url, engine
    except OperationalError as exc:
        logger.warning(
            "Could not connect to DATABASE_URL (%s): %s. Falling back to SQLite at %s",
            database_url,
            exc.orig or exc,
            DEFAULT_SQLITE_URL,
        )
        return DEFAULT_SQLITE_URL, _create_engine(DEFAULT_SQLITE_URL)

DATABASE_URL, engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that provides a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
