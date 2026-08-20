"""Point d'entrée FastAPI : montage des routes, CORS, healthcheck, lifespan."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcpgen.api.deps import init_session_factory
from mcpgen.api.routes import chat, generate, servers, swagger
from mcpgen.core.config import Settings, get_settings
from mcpgen.core.logging import get_logger, setup_logging
from mcpgen.models import db_models  # noqa: F401  (enregistre les modèles)
from mcpgen.models.db_models import init_db

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fabrique l'application FastAPI (utilisée par uvicorn et les tests)."""
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine, factory = init_db(settings.database_url)
        init_session_factory(factory)
        settings.generated_servers_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "application_started",
            extra={"extra_fields": {"version": "0.1.0", "env": settings.app_env}},
        )
        yield
        engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Générateur de serveurs MCP à partir d'une spec Swagger/OpenAPI",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(swagger.router)
    app.include_router(generate.router)
    app.include_router(servers.router)
    app.include_router(chat.router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "version": "0.1.0"}

    @app.get("/")
    def root() -> dict:
        return {"name": settings.app_name, "docs": "/docs", "health": "/health"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "mcpgen.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
    )
