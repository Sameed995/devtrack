import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _create_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def _build_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    engine = _create_engine(database_url)
    logger.info("Connected to PostgreSQL database")
    return database_url, engine

DATABASE_URL, engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_schema() -> None:
    """Best-effort schema tweaks for simple deployments (no Alembic).

    SQLAlchemy's create_all() won't add columns to existing tables, so we
    apply small, idempotent ALTERs here.
    """

    statements = [
        "ALTER TABLE endpoints ADD COLUMN IF NOT EXISTS interval_minutes INTEGER",
        "ALTER TABLE endpoints ADD COLUMN IF NOT EXISTS interval_seconds INTEGER",
        "ALTER TABLE endpoints ADD COLUMN IF NOT EXISTS user_id INTEGER",
        # Remove global URL uniqueness (new behavior is per-user uniqueness).
        "ALTER TABLE endpoints DROP CONSTRAINT IF EXISTS endpoints_url_key",
        # Add FK + composite unique in an idempotent way.
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_endpoints_user_id') THEN
                ALTER TABLE endpoints
                    ADD CONSTRAINT fk_endpoints_user_id
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_endpoints_user_url') THEN
                ALTER TABLE endpoints
                    ADD CONSTRAINT uq_endpoints_user_url
                    UNIQUE (user_id, url);
            END IF;
        END
        $$;
        """,
    ]

    try:
        with engine.connect() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()
    except Exception:
        # Don't block app startup if the DB user lacks ALTER permissions.
        logger.exception("Schema ensure step failed")


def get_db():
    """FastAPI dependency that provides a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
