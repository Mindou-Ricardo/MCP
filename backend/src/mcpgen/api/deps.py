"""Dépendances FastAPI partagées (session DB, settings)."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from mcpgen.core.config import Settings, get_settings

_session_factory: sessionmaker | None = None


def init_session_factory(factory: sessionmaker) -> None:
    """Initialise la session factory (appelé au lifespan de l'app)."""
    global _session_factory
    _session_factory = factory


def get_session_factory() -> sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Session factory non initialisée (lifespan ?)")
    return _session_factory


def get_db(factory: sessionmaker = Depends(get_session_factory)) -> Generator[Session, None, None]:
    """Dépendance FastAPI : session SQLAlchemy."""
    with factory() as session:
        yield session


def get_db_factory() -> sessionmaker:
    return get_session_factory()


def get_app_settings() -> Settings:
    return get_settings()
