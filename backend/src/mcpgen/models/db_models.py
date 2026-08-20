"""Modèles SQLAlchemy (SQLite par défaut, migrable vers Postgres)."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class ServerStatus(enum.StrEnum):
    pending = "pending"
    generating = "generating"
    ready = "ready"
    regenerating = "regenerating"
    failed = "failed"


class SwaggerSpec(Base):
    """Spécification Swagger/OpenAPI importée (fichier ou URL)."""

    __tablename__ = "swagger_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(16))  # file | url
    content: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    openapi_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    endpoints_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    servers: Mapped[list[GeneratedServer]] = relationship(
        back_populates="spec", cascade="all, delete-orphan"
    )


class GeneratedServer(Base):
    """Serveur MCP généré à partir d'une spec."""

    __tablename__ = "generated_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    auth_type: Mapped[str] = mapped_column(String(32), default="none")  # none|api_key|bearer|basic
    auth_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    endpoints: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of names
    endpoints_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ServerStatus] = mapped_column(Enum(ServerStatus), default=ServerStatus.pending)
    dir_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    spec_id: Mapped[int | None] = mapped_column(
        ForeignKey("swagger_specs.id", ondelete="SET NULL"), nullable=True
    )
    spec: Mapped[SwaggerSpec | None] = relationship(back_populates="servers")


def create_db_engine(database_url: str):
    """Crée l'engine SQLAlchemy selon l'URL (SQLite par défaut)."""
    kwargs: dict = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **kwargs)


def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db(database_url: str) -> tuple:
    """Crée les tables et retourne (engine, session_factory)."""
    engine = create_db_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine, create_session_factory(engine)
