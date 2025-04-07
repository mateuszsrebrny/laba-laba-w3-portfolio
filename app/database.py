from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()

# Lazy instantiation
_engine = None
_SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    global _engine, _SessionLocal

    settings = get_settings()

    if _engine is None or _SessionLocal is None:
        connect_args = (
            {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            future=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

    db = _SessionLocal()

    try:
        yield db
    finally:
        db.close()
